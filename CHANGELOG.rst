CHANGELOG
=========

version 1.0.0
+++++++++++++

* First official release
* Add forgotten delete trigger on `gn_synthese.synthese`

version 0.1.2-dev
+++++++++++++++++

* Fix ``error_count`` type. cf. issue `gn2pg_import - error_count donnée en entrée invalide #18 <https://github.com/lpoaura/GN2PG/issues/18>`_


version 0.1.1-dev
+++++++++++++++++

* Fix wrong log function name (previously renamed download_log). cf. issue `StorePostgresql object has no attribute log #17  <https://github.com/lpoaura/GN2PG/issues/17>`_.

version 0.1.0-dev
+++++++++++++++++

* new feature: incremental update


version 0.0.5-dev
+++++++++++++++++

* Refactor app name to GN2PG
* fix custom-script that start anytime after --init commands.
* update logos


version 0.0.4-dev
+++++++++++++++++

* Log dowload error in db table
* Add sql custom scripts option to auto populate GeoNature db (provided by default) or anything else.

version 0.0.3-dev
+++++++++++++++++

* Dockerize app
* Cleanup code
* Refactor submodules names
* Improve docs

version 0.0.2-dev
+++++++++++++++++

* Download and store data by offset pages.
* Code cleanup.


version 0.0.1-dev
+++++++++++++++++

First pre-release with full download implemented.
This release download all data from API then store in database
