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
from openerp.osv import fields, orm
try:
    from server_environment import serv_config
except ImportError:
    logging.getLogger('openerp.module').warning(
        'server_environment not available in addons path. '
        'server_env_elasticsearch_view_export will not be usable')

_logger = logging.getLogger(__name__)


class ElasticsearchHost(orm.Model):
    _inherit = 'elasticsearch.host'

    def _get_environment_config_by_name(self, cr, uid, ids, field_names,
                                        arg, context=None):
        values = {}
        for host in self.browse(cr, uid, ids, context=context):
            values[host.id] = {}
            for field_name in field_names:
                values[host.id][field_name] = False
                if not host.code:
                    continue
                section_name = '.'.join((self._name.replace('.', '_'),
                                         host.code))
                try:
                    value = serv_config.get(section_name, field_name)
                    values[host.id][field_name] = value
                except:
                    _logger.exception('error trying to read field %s '
                                      'in section %s', field_name,
                                      section_name)
        return values

    _columns = {
        'code': fields.char(string='Code', required=True,
                            help="Code which is used to identify this "
                                 "record in the 'server_environment' "
                                 "configuration file."),
        'host': fields.function(
            _get_environment_config_by_name,
            string='Host',
            type='char',
            multi='connection_config'),
    }
