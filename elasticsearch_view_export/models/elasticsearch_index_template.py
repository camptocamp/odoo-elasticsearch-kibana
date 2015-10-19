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
import json

from elasticsearch.exceptions import TransportError

from openerp.osv import orm, fields
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)


class ElasticsearchIndexTemplate(orm.Model):
    _name = 'elasticsearch.index.template'
    _description = 'Elasticsearch Index Template'

    _columns = {
        'name': fields.char(string='Template Name', required=True),
        'template': fields.text(string='Template', required=True),
        'host_id': fields.many2one('elasticsearch.host',
                                   string='Hosts',
                                   required=True),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('done', 'Indexed'),
             ],
            string='State',
            readonly=True,
        ),
    }

    _defaults = {
        'state': 'draft',
    }

    def _check_template(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            try:
                json.dumps(record.template)
            except ValueError:
                return False
        return True

    _constraints = [
        (_check_template,
         'The template must be a valid JSON.',
         ['template']),
    ]

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         'Another template has the same name.')
    ]

    def refresh_template(self, cr, uid, ids, context=None):
        for index_template in self.browse(cr, uid, ids, context=context):
            self._es_refresh_template(cr, uid, index_template, context=context)
            index_template.write({'state': 'done'})

    def drop_template(self, cr, uid, ids, context=None):
        for index_template in self.browse(cr, uid, ids, context=context):
            self._es_drop_template(cr, uid, index_template, context=context)
            index_template.write({'state': 'draft'})

    def _es_drop_template(self, cr, uid, index_template, context=None):
        es = index_template.host_id._es_client()
        if es.indices.exists_template(index_template.name):
            _logger.info("Dropping template '%s' on %s",
                         index_template.name, es)
            es.indices.delete_template(index_template.name)

    def _es_refresh_template(self, cr, uid, index_template, context=None):
        es = index_template.host_id._es_client()
        _logger.info("Updating template '%s' on %s", index_template.name, es)

        try:
            result = es.indices.put_template(index_template.name,
                                             body=index_template.template)
        except TransportError as err:
            raise orm.except_orm(
                _('Error'),
                _('Could not create the '
                  'template %s on Elasticsearch:\n\n%s' % (index_template.name,
                                                           err,))
            )
        return result

    def unlink(self, cr, uid, ids, context=None):
        for index_template in self.browse(cr, uid, ids, context=context):
            if index_template.state == 'done':
                raise orm.except_orm(
                    _('Error'),
                    _('Please drop the template on Elasticsearch before '
                      'deleting this record.')
                )
        _super = super(ElasticsearchIndexTemplate, self)
        return _super.unlink(cr, uid, ids, context=context)
