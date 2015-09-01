# -*- coding: utf-8 -*-
#
#
#    Authors: Guewen Baconnier
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

import logging

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError
from elasticsearch.exceptions import TransportError

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

BULK_CHUNK_SIZE = 1000  # records at a time


class ElasticSearchViewIndex(orm.Model):
    _name = 'elasticsearch.view.index'
    _description = 'ElasticSearch View Index'

    def _selection_sql_view(self, cr, uid, context=None):
        cr.execute(
            "SELECT viewname FROM pg_catalog.pg_views "
            "WHERE schemaname NOT IN ('pg_catalog', 'information_schema') "
            "ORDER BY schemaname, viewname"
        )
        return [(row[0], row[0]) for row in cr.fetchall()]

    _columns = {
        'name': fields.char(string='Index Name', required=True),
        'host_id': fields.many2one('elasticsearch.host',
                                   string='Hosts',
                                   required=True),
        'sql_view': fields.selection(_selection_sql_view,
                                     string='View',
                                     required=True),
        'refresh_interval_type': fields.selection(
            [('hourly', 'Hour(s)'),
             ('daily', 'Day(s)'),
             ('weekly', 'Week(s)'),
             ('monthly', 'Month(s)'),
             ('yearly', 'Year(s)'),
             ],
            string='Interval Type',
            required=True,
        ),
        'refresh_interval': fields.integer(
            string="Refresh Every",
            help="Refresh every (Days/Week/Month/Year)",
            required=True,
        ),
        'refresh_next': fields.datetime('Date of next refresh',
                                        required=True),
    }

    def _default_refresh_next(self, cr, uid, context=None):
        """ Initialize next day at midnight

        So it won't create the index directly when we edit and we better
        have to run it during the night.
        """
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d 00:00:00")

    _defaults = {
        'refresh_interval': 1,
        'refresh_next': _default_refresh_next,
        'refresh_interval_type': 'daily'
    }

    def refresh_index(self, cr, uid, ids, context=None):
        return self._refresh_index(cr, uid, ids, context=context)

    def _cron_refresh_index(self, cr, uid, context=None):
        return self._refresh_index(cr, uid, [], automatic=True,
                                   context=context)

    def _refresh_index(self, cr, uid, ids, automatic=False, context=None):
        if not ids:
            domain = [('refresh_next', '<=', fields.datetime.now())]
            ids = self.search(cr, uid, domain, context=context)
        for view_index in self.browse(cr, uid, ids, context=context):
            self._es_create_index(cr, uid, view_index, context=context)
            if automatic:
                next_date = datetime.strptime(view_index.refresh_next,
                                              DEFAULT_SERVER_DATETIME_FORMAT)
                interval = view_index.refresh_interval
                if view_index.refresh_interval_type == 'hourly':
                    new_date = next_date + relativedelta(hours=+interval)
                elif view_index.refresh_interval_type == 'daily':
                    new_date = next_date + relativedelta(days=+interval)
                elif view_index.refresh_interval_type == 'weekly':
                    new_date = next_date + relativedelta(weeks=+interval)
                elif view_index.refresh_interval_type == 'monthly':
                    new_date = next_date + relativedelta(months=+interval)
                else:
                    new_date = next_date + relativedelta(years=+interval)
                view_index.write({'refresh_next': new_date})
        return True

    def _es_index_data(self, cr, uid, view_index, context=None):
        cr.execute("SELECT * FROM %s" % view_index.sql_view)
        for row in cr.dictfetchall():
            yield {'_index': view_index.name,
                   '_type': 'document',
                   '_source': row}

    def _es_client(self, cr, uid, view_index, context=None):
        return Elasticsearch([view_index.host_id.host])

    def _es_create_index(self, cr, uid, view_index, context=None):
        es = self._es_client(cr, uid, view_index, context=context)
        _logger.info("Creating index '%s' on %s", view_index.name, es)
        if es.indices.exists(index=view_index.name):
            es.indices.delete(index=view_index.name)

        # TODO: param
        request_body = {
            'settings': {
                'number_of_shards': 1,
                'number_of_replicas': 0,
            }
        }
        try:
            es.indices.create(index=view_index.name,
                              body=request_body)
        except TransportError as err:
            raise orm.except_orm(
                _('Error'),
                _('Could not create the '
                  'index on ElasticSearch:\n\n%s' % (err,))
            )
        index_data = self._es_index_data(cr, uid, view_index, context=context)
        try:
            result = bulk(es, index_data, chunk_size=BULK_CHUNK_SIZE)
        except TransportError as err:
            raise orm.except_orm(
                _('Error'),
                _('Could not send data on the '
                  'index on ElasticSearch:\n\n%s' % (err,))
            )
        except BulkIndexError as err:
            raise orm.except_orm(
                _('Error'),
                _('Could not index the view %s '
                  'on ElasticSearch:\n\n%s' % (view_index.name, err,))
            )
        return result

        # TODO: unlink, renaming of index
