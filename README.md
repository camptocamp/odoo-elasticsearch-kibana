[![Build Status](https://travis-ci.org/camptocamp/odoo-elasticsearch-kibana.svg?branch=7.0)](https://travis-ci.org/camptocamp/odoo-elasticsearch-kibana)
[![Coverage Status](https://coveralls.io/repos/camptocamp/odoo-elasticsearch-kibana/badge.png?branch=7.0)](https://coveralls.io/r/camptocamp/odoo-elasticsearch-kibana?branch=7.0)

Odoo Elasticsearch & Kibana
===========================

Odoo addons related to Elasticsearch and Kibana.
The addons here are in an early stage of development and specific to our use cases.
Once they are mature enough, they should be proposed to the OCA (https://github.com/OCA)

The principle is to build SQL views of the required row data in Odoo and push them into a given index in Elasticsearch. Then you can use the power of Kibana to explore the data and build dashboard. The response time is impressiv even with billion of records.

We use alongside those module this one https://github.com/OCA/server-tools/tree/7.0/sql_view in order to be able to write SQL view directly from Odoo interface.
