# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

<!-- ## Unreleased [{version_tag}](https://github.com/opengisch/qgis-plugin-ci/releases/tag/{version_tag}) - YYYY-MM-DD -->

## 1.6.7 - 2024-10-07

### Fixes

- Populate `additional_data` (if column exists) on `gn_meta.t_datasets`, `gn_meta.t_acquisition_frameworks` and `gn_synthese.t_sources`,fix #87
- Replace module `pkg_resouces` by native `importlib`, fix #88
- Add default values for missing many to many relations on acquisition frameworks, fix #92

TODO: For users who use gn2pg to populate a GeoNature db, you should update sql scripts.

```
pip install --upgrade gn2pg-client
gn2pg_cli --custom-script=to_gnsynthese myconfig.toml
```

## 1.6.6 - 2024-08-20

### Fixes

- Pagination is now calculated from API response (`limit` value), fix #81

## 1.6.5 - 2024-06-10

### Fixes

- Fix trigger to populate additional data (fix #73).

## 1.6.4 - 2024-04-24

### Fixes

- Fix typo error on trigger scripts.

## 1.6.3 - 2024-04-11

### What's Changed

- Fix #65, delete don't work when source contains upper case or special characters

## 1.6.2 - 2024-04-08

### What's Changed

- Manage additional_data values in triggers to import data into synthese.
- use GitHub pages
- new GitHub workflows

## 1.6.1 - 2024-01-23

### What's Changed

- fix readthedocs config
- update dependencies

## 1.6.0 - 2023-09-27

### What's Changed
* fix email conflict error on t_roles by not populating email by @lpofredc in https://github.com/lpoaura/GN2PG/pull/46
* fix Erreur en fin d'update sur 'total_filtered' https://github.com/lpoaura/GN2PG/issues/49

### ❗  Caution

If GeoNature sources are on latest versions (v2.13.x), ensure that Utils-Flask-SQLAlchemy is version 0.3.6+ as mentionned in https://github.com/lpoaura/GN2PG/issues/48.

### 📝  Update

```bash
pip install --upgrade gn2pg-client
```
If client database is a GeoNature DB, apply last SQL Scripts
```bash
gn2pg_cli --custom-script to_gnsynthese <myconfigfile>
```

## 1.5.1 - 2023-05-29

- refactor: mutualize triggers/functions for upsert into GeoNature database (#44)

With the financial support of [Office français de la biodiversité](https://www.ofb.gouv.fr).

TODO after upgrade: \*\*

Delete triggers and functions on destination database.

```sql
DROP TRIGGER IF EXISTS tri_c_upsert_data_to_geonature_with_nomenclature_label ON gn2pg_import.data_json;
DROP TRIGGER IF EXISTS tri_c_upsert_data_to_geonature_with_cd_nomenclature ON gn2pg_import.data_json;
DROP TRIGGER IF EXISTS tri_c_upsert_data_to_geonature_with_metadata ON gn2pg_import.data_json;
DROP TRIGGER IF EXISTS tri_c_delete_data_from_geonature ON gn2pg_import.data_json;

DROP FUNCTION IF EXISTS gn2pg_import.fct_c_get_or_insert_basic_af_from_uuid_name(_uuid UUID, _name TEXT);
DROP FUNCTION IF EXISTS gn2pg_import.fct_c_get_or_insert_basic_dataset_from_uuid_name(_uuid UUID, _name TEXT, _id_af INT);
DROP FUNCTION IF EXISTS gn2pg_import.fct_c_get_or_insert_source(_source TEXT);
DROP FUNCTION IF EXISTS gn2pg_import.fct_c_get_id_nomenclature_from_label(_type TEXT, _label TEXT);
DROP FUNCTION IF EXISTS gn2pg_import.fct_tri_c_upsert_data_to_geonature_with_nomenclature_label();
DROP FUNCTION IF EXISTS gn2pg_import.fct_tri_c_upsert_data_to_geonature_with_cd_nomenclature();
DROP FUNCTION IF EXISTS gn2pg_import.fct_tri_c_delete_data_from_geonature();
DROP FUNCTION IF EXISTS gn2pg_import.fct_c_insert_ds_territories(_id_ds INTEGER, _territories JSONB) ;
DROP FUNCTION IF EXISTS gn2pg_import.fct_c_get_or_create_actors_in_usershub(_actor_role JSONB, _source CHARACTER VARYING) ;
DROP FUNCTION IF EXISTS gn2pg_import.fct_c_insert_dataset_actor(_id_dataset INTEGER, _actor_roles JSONB, _source CHARACTER VARYING);
DROP FUNCTION IF EXISTS gn2pg_import.fct_c_insert_af_actors(_id_af INTEGER, _actor_roles JSONB, _source CHARACTER VARYING) ;
DROP FUNCTION IF EXISTS gn2pg_import.fct_c_get_or_insert_af_from_af_jsondata(_af_data JSONB, _source CHARACTER VARYING);
DROP FUNCTION IF EXISTS gn2pg_import.fct_c_get_or_insert_dataset_from_jsondata(_ds_data JSONB, _id_af INTEGER, _source CHARACTER VARYING);
DROP FUNCTION IF EXISTS gn2pg_import.fct_c_get_or_insert_source(_source TEXT);
DROP FUNCTION IF EXISTS gn2pg_import.fct_tri_c_upsert_data_to_geonature_with_metadata();
DROP FUNCTION IF EXISTS gn2pg_import.fct_tri_c_delete_data_from_geonature();
```

Apply new to_gnsynthese.sql script.

```bash
gn2pg_cli --custom-script to_gnsynthese <myconfigfile>
```

## 1.5.0

- New web dashboard using flask-admin (#39)

With the financial support of [Office français de la biodiversité](https://www.ofb.gouv.fr).

## version 1.4.0

- Optimization and code factorization (#27 / #29)
- Add automatic tests (#29)
- Improve performances with parallelization of API calls with multithreading (#27 / #30)
- Fix missing custom query strings on updates
- Update base image version in Docker
- Update dependencies

With the financial support of [Office français de la biodiversité](https://www.ofb.gouv.fr).

## version 1.3.0

- Add optional query strings on API calls, almost required to order export API using key `orderby`

## version 1.2.0

- Update dependencies
- Removal of requests to assign an owner to functions, cause of errors
- Set `gn2pg_import` as default schema name in config template
- Fix custom-script command on default to_gnsynthese.sql script due to `%` character
- Improve t_roles populate on a GeoNature database using json objects with first and last name
- Fix missing validation status on exports samples

## version 1.1.2

- Fix null value in `gn_synthese.synthese.the_geom_local` caused by null SRID value while getting SRID from first data in `gn_synthese.synthese`.

## version 1.1.1

- Fix delete trigger on synthese standard data (`synthese_with_metadata` type missing).

## version 1.1.0

- New SQL scripts for geonature 2 geonature imports which provide triggers to insert data in synthese and populate most of the metadata data (acquisition frameworks, datasets, actors such as organisms and roles, territories, etc.). Source query sample is provided in file [geonature_export_sinp_with_metadata.sql](https://github.com/lpoaura/GN2PG/tree/main/data/source_samples/geonature_export_sinp_with_metadata.sql)

## version 1.0.1

- Fix custom-script error due to % character in sql script (RAISE INFO command).
- Update dependencies

## version 1.0.0

- First official release
- Add forgotten delete trigger on `gn_synthese.synthese`

## version 0.1.2-dev

- Fix `error_count` type. cf. issue [gn2pg_import - error_count donnée en entrée invalide #18](https://github.com/lpoaura/GN2PG/issues/18)

## version 0.1.1-dev

- Fix wrong log function name (previously renamed download_log). cf. issue [StorePostgresql object has no attribute log #17](https://github.com/lpoaura/GN2PG/issues/17).

## version 0.1.0-dev

- new feature: incremental update

## version 0.0.5-dev

- Refactor app name to GN2PG
- fix custom-script that start anytime after --init commands.
- update logos

## version 0.0.4-dev

- Log dowload error in db table
- Add sql custom scripts option to auto populate GeoNature db (provided by default) or anything else.

## version 0.0.3-dev

- Dockerize app
- Cleanup code
- Refactor submodules names
- Improve docs

## version 0.0.2-dev

- Download and store data by offset pages.
- Code cleanup.

## version 0.0.1-dev

First pre-release with full download implemented.
This release download all data from API then store in database
