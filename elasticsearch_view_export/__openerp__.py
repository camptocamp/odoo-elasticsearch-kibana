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

{'name': 'ElasticSearch Views Exporter',
 'version': '1.0',
 'author': 'Camptocamp',
 'license': 'AGPL-3',
 'category': 'Tools',
 'depends': ['base'],
 'description': """
============================
ElasticSearch Views Exporter
============================

Allows to create indexes on ElasticSearch based on views.

Usage
=====

 """,
 'website': 'http://www.camptocamp.com',
 'external_dependencies': {'python': ['elasticsearch']},
 'data': ['views/elasticsearch_host_views.xml',
          'views/elasticsearch_view_index_views.xml',
          'data/elasticsearch_cron.xml',
          'security/ir.model.access.csv',
          ],
 'installable': True,
 }
