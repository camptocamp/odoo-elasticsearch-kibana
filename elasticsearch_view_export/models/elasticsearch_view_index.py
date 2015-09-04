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

import json
import logging

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from elasticsearch.helpers import bulk, BulkIndexError
from elasticsearch.exceptions import TransportError

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

BULK_CHUNK_SIZE = 500  # records at a time


class ElasticsearchViewIndex(orm.Model):
    _name = 'elasticsearch.view.index'
    _description = 'Elasticsearch View Index'
    _inherit = ['mail.thread']

    def _selection_sql_view(self, cr, uid, context=None):
        cr.execute(
            "SELECT c.relname AS viewname, "
            "       obj_description(c.oid) "
            "   FROM pg_class c "
            "     LEFT JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE c.relkind IN ('v', 'm') "
            "AND n.nspname NOT IN ('pg_catalog', 'information_schema')"
        )
        selection = []
        for row in cr.fetchall():
            view_name = row[0]
            comment = row[1]
            if comment:
                descr = "%s <%s>" % (view_name, comment)
            else:
                descr = view_name
            selection.append((view_name, descr))
        return selection

    _columns = {
        'name': fields.char(string='Index Name', required=True),
        'host_id': fields.many2one('elasticsearch.host',
                                   string='Hosts',
                                   required=True),
        'sql_view': fields.selection(_selection_sql_view,
                                     string='View',
                                     required=True),
        'refresh_auto': fields.boolean('Automatic Refresh'),
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
        'index_config': fields.text('Index Configuration'),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('done', 'Indexed'),
             ],
            string='State',
            readonly=True,
        ),
    }

    def _default_refresh_next(self, cr, uid, context=None):
        """ Initialize next day at midnight

        So it won't create the index directly when we edit and we better
        have to run it during the night.
        """
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d 00:00:00")

    _defaults = {
        'refresh_auto': True,
        'refresh_interval': 1,
        'refresh_next': _default_refresh_next,
        'refresh_interval_type': 'daily',
        'state': 'draft',
        'index_config': '{}',
    }

    def _check_index_config(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if not record.index_config:
                continue
            try:
                json.dumps(record.index_config)
            except ValueError:
                return False
        return True

    _constraints = [
        (_check_index_config,
         'The index configuration must be a valid JSON.',
         ['index_config']),
    ]

    def refresh_index(self, cr, uid, ids, context=None):
        return self._refresh_index(cr, uid, ids, context=context)

    def drop_index(self, cr, uid, ids, context=None):
        for view_index in self.browse(cr, uid, ids, context=context):
            es = view_index.host_id._es_client()
            _logger.info("Dropping index '%s' on %s", view_index.name, es)
            self._es_drop_index(cr, uid, view_index, es, context=context)
            view_index.write({'state': 'draft'})

    def _cron_refresh_index(self, cr, uid, context=None):
        return self._refresh_index(cr, uid, [], automatic=True,
                                   context=context)

    def _refresh_index(self, cr, uid, ids, automatic=False, context=None):
        if not ids:
            domain = [('refresh_auto', '=', True),
                      ('refresh_next', '<=', fields.datetime.now())]
            ids = self.search(cr, uid, domain, context=context)
        for view_index in self.browse(cr, uid, ids, context=context):
            values = {}
            try:
                self._es_refresh_index(cr, uid, view_index, context=context)
            except Exception as err:
                if not automatic:
                    raise
                # when it runs from a cron, we want to log any error
                # that could happen so the user is aware that the
                # indexing didn't work
                _logger.exception('Error when indexing on Elasticsearch')
                if isinstance(err, orm.except_orm):
                    err = err[1]
                msg = _('Indexing on Elasticsearch failed.\n\n%s') % (err,)
                self.message_post(cr, uid, view_index.id, body=msg,
                                  context=context)
                # even if it failed, we want to continue and update the
                # 'refresh_next' date so it will be retried next time
            else:
                values['state'] = 'done'

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
                values['refresh_next'] = new_date
            view_index.write(values)
            if automatic:
                cr.commit()
        return True

    def _es_index_data(self, cr, uid, view_index, context=None):
        cr.execute("SELECT * FROM %s" % view_index.sql_view)
        columns = [desc[0] for desc in cr.description]
        while 1:
            rows = cr.fetchmany(BULK_CHUNK_SIZE)
            if not rows:
                break
            for row in rows:
                yield {'_index': view_index.name,
                       '_type': 'document',
                       '_source': dict(zip(columns, row))}

    def _es_drop_index(self, cr, uid, view_index, es, context=None):
        if es.indices.exists(index=view_index.name):
            es.indices.delete(index=view_index.name)

    def _es_refresh_index(self, cr, uid, view_index, context=None):
        es = view_index.host_id._es_client()
        try:
            self._es_drop_index(cr, uid, view_index, es, context=context)
        except TransportError as err:
            raise orm.except_orm(
                _('Error'),
                _('Could not delete the '
                  'index on Elasticsearch:\n\n%s' % (err,))
            )
        _logger.info("Creating index '%s' on %s", view_index.name, es)

        try:
            es.indices.create(index=view_index.name,
                              body=view_index.index_config)
        except TransportError as err:
            raise orm.except_orm(
                _('Error'),
                _('Could not create the '
                  'index on Elasticsearch:\n\n%s' % (err,))
            )
        index_data = self._es_index_data(cr, uid, view_index, context=context)
        try:
            result = bulk(es, index_data, chunk_size=BULK_CHUNK_SIZE)
        except TransportError as err:
            raise orm.except_orm(
                _('Error'),
                _('Could not send data on the '
                  'index on Elasticsearch:\n\n%s' % (err,))
            )
        except BulkIndexError as err:
            raise orm.except_orm(
                _('Error'),
                _('Could not index the view %s '
                  'on Elasticsearch:\n\n%s' % (view_index.name, err,))
            )
        return result
