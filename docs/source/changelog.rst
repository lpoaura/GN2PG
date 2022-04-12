CHANGELOG
=========

version 1.1.1
+++++++++++++

* Fix delete trigger on synthese standard data (`synthese_with_metadata` type missing).

version 1.1.0
+++++++++++++

* New SQL scripts for geonature 2 geonature imports which provide triggers to insert data in synthese and populate most of the metadata data (acquisition frameworks, datasets, actors such as organisms and roles, territories, etc.). Source query sample is provided in file `geonature_export_sinp_with_metadata.sql <https://github.com/lpoaura/GN2PG/tree/main/data/source_samples/geonature_export_sinp_with_metadata.sql>`_ 

version 1.0.1
+++++++++++++

* Fix custom-script error due to % character in sql script (RAISE INFO command).
* Update dependencies

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
