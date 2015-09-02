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

{'name': 'Elasticsearch Views Exporter',
 'version': '1.0',
 'author': 'Camptocamp',
 'license': 'AGPL-3',
 'category': 'Tools',
 'depends': ['mail',
             ],
 'description': """
============================
Elasticsearch Views Exporter
============================

Allows to create indexes on Elasticsearch based on views.

It supports one view per index and each index is created using a
``SELECT * FROM ...`` on the selected view.

The only synchronisation strategy available is one-shot with possible
automatic refreshes. Meaning that at every refresh the index is dropped and
regenerated completely.

Usage
=====

Menu entries are:

* Settings > Technical > Elasticsearch
* Settings > Technical > Elasticsearch > Hosts: configuration of the
  Elasticsearch hosts
* Settings > Technical > Elasticsearch > View Indexes: configuration of
  the indexes

 """,
 'website': 'http://www.camptocamp.com',
 'external_dependencies': {'python': ['elasticsearch']},
 'data': ['views/elasticsearch_menus.xml',
          'views/elasticsearch_host_views.xml',
          'views/elasticsearch_view_index_views.xml',
          'data/elasticsearch_cron.xml',
          'security/ir.model.access.csv',
          ],
 'installable': True,
 }
