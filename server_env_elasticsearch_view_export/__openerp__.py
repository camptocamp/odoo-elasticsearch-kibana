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

{'name': 'Server Environment for Elasticsearch Views Exporter',
 'version': '1.0',
 'author': 'Camptocamp',
 'license': 'AGPL-3',
 'category': 'Tools',
 'depends': ['elasticsearch_view_export',
             'server_environment',
             ],
 'description': """
Server Environment for Elasticsearch Views Exporter
===================================================

This module is based on the `server_environment` module to use files for
configuration.  Thus we can have a different configuration for each
environment (dev, test, staging, prod).  This module defines the config
variables for the `elasticsearch_view_export` module.

In the configuration file, you can configure the host address of the
Elasticsearch server.

Exemple of the section to put in the configuration file::

    [elasticsearch_host.code_of_the_host]
    host = http://localhost:9200

 """,
 'website': 'http://www.camptocamp.com',
 'data': ['elasticsearch_host_views.xml',
          ],
 'test': [],
 'installable': True,
 'auto_install': True,
 }
