# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

<!-- ## Unreleased [{version_tag}](https://github.com/opengisch/qgis-plugin-ci/releases/tag/{version_tag}) - YYYY-MM-DD -->

## 1.9.0-dev - 2025-05-xx

### :rocket: Features

- For exports of type `synthese_with_metadata`, Metadata are now stored separately in `gn2pg_import.metadata_json` table (fix #116).
- Import history is now stored in a single table (`import_log`) containing execution information such as download type (full or update), import statistics for API, data and metadata (fix #111).
- When an update is launched (`gn2pg_cli db --update`), if no import exists for a specific source, a complete download is launched for that source. It is no longer necessary to run a `--full` download after adding a new source.
- While inserting data into GeoNature, default nomenclature is used when no nomenclature is provided or if nomenclature is not matching current database (fix #107)
- Add management if area_attachment. If no area is matching in destination db, `type_info_geo` is set to `Géoréférencement` else, to `Rattachement`(fix #106).

### :bug: Fixes

- Fix log history API call using parameter `page` instead of `offset` (fix #117)

### :point_down: Release note

To do for update (only)

> [!WARNING]
> Providers should update their export scripts as in sample to embed area_attachment informations: [geonature_export_sinp_with_metadata.sql](./data/geonature_export_sinp_with_metadata.sql)


1. Update the app

```bash
pip install --upgrade gn2pg-client
gn2pg_cli db --json-tables-create <config file>
```

2. Add a unique constraint on data_json.uuid table (if not already added after upgrade to 1.8.0):

```sql
BEGIN;

SET SESSION_REPLICATION_ROLE TO replica;

ALTER TABLE gn2pg_import.data_json
    ADD import_id INT REFERENCES gn2pg_import.import_log ON UPDATE CASCADE;

ALTER TABLE gn2pg_import.error_log
    ADD import_id INT REFERENCES gn2pg_import.import_log ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE gn2pg_import.error_log
    ADD uuid uuid;

UPDATE gn2pg_import.error_log
SET uuid = COALESCE(item ->> 'id_perm_sinp', item ->> 'uuid')::uuid;

ALTER TABLE gn2pg_import.error_log
    ALTER COLUMN uuid SET NOT NULL;

UPDATE gn2pg_import.data_json
SET import_id = import_log.id
FROM gn2pg_import.import_log
WHERE import_log.source = data_json.source;

UPDATE gn2pg_import.error_log
SET import_id = import_log.id
FROM gn2pg_import.import_log
WHERE import_log.source = error_log.source;

WITH af AS (SELECT item -> 'ca_data' FROM gn2pg_import.data_json);

WITH history AS (SELECT source
                      , controler
                      , download_ts AS xfer_start_ts
                 FROM gn2pg_import.download_log
                 UNION
                 SELECT source
                      , controler
                      , last_ts AS xfer_start_ts
                 FROM gn2pg_import.increment_log)
   , hunion AS (SELECT source, controler, MAX(xfer_start_ts) xfer_start_ts FROM history GROUP BY source, controler)
INSERT
INTO gn2pg_import.import_log ( source, controler, xfer_type, xfer_status, xfer_start_ts, data_count_upserts
                             , xfer_http_status, "comment")
SELECT hunion.source
     , hunion.controler
     , 'full'             AS xfer_type
     , 'success'          AS xfer_status
     , hunion.xfer_start_ts
     , COUNT(data_json.*) AS data_count_upserts
     , '200'              AS xfer_http_status
     , 'Line generated on upgrade to gn2pg 1.9 or above'
FROM hunion
         JOIN gn2pg_import.data_json ON (data_json.source, data_json.controler) = (hunion.source, hunion.controler)
GROUP BY hunion.source, hunion.controler, hunion.xfer_start_ts
ORDER BY xfer_start_ts ASC
;

INSERT INTO gn2pg_import.metadata_json(uuid, source, controler, type, level, item, import_id, update_ts)
WITH af AS (SELECT data_json.item #>> '{ca_data,uuid}'                         uuid
                 , source
                 , 'metadata'                                               AS controler
                 , data_json.type
                 , 'acquisition framework'                                     level
                 , (ARRAY_AGG(item -> 'ca_data' ORDER BY update_ts ASC))[1] AS item
                 , (ARRAY_AGG(import_id ORDER BY update_ts ASC))[1]         AS import_id
                 , (ARRAY_AGG(update_ts ORDER BY update_ts ASC))[1]         AS update_ts
            FROM gn2pg_import.data_json
            GROUP BY data_json.item #>> '{ca_data,uuid}', source, data_json.type)
   , ds AS (SELECT data_json.item #>> '{jdd_data,uuid}'                         uuid
                 , source
                 , 'metadata'                                                AS controler
                 , data_json.type
                 , 'dataset'                                                    level
                 , (ARRAY_AGG(item -> 'jdd_data' ORDER BY update_ts ASC))[1] AS item
                 , (ARRAY_AGG(import_id ORDER BY update_ts ASC))[1]          AS import_id
                 , (ARRAY_AGG(update_ts ORDER BY update_ts ASC))[1]          AS update_ts
            FROM gn2pg_import.data_json
            GROUP BY data_json.item #>> '{jdd_data,uuid}', source, data_json.type)
   , metaunion AS (SELECT uuid
                        , source
                        , controler
                        , type
                        , level
                        , item
                        , import_id
                        , update_ts
                   FROM af
                   UNION
                   SELECT uuid
                        , source
                        , controler
                        , type
                        , level
                        , item
                        , import_id
                        , update_ts
                   FROM ds)
SELECT uuid::uuid
     , source
     , controler
     , type
     , level
     , item
     , import_id
     , update_ts
FROM metaunion
ORDER BY update_ts ASC
ON CONFLICT (uuid) DO NOTHING;

ALTER TABLE gn2pg_import.data_json
    ALTER COLUMN import_id SET NOT NULL;

ALTER TABLE gn2pg_import.error_log
    ALTER COLUMN import_id SET NOT NULL;

ALTER TABLE gn2pg_import.error_log
    ALTER COLUMN uuid SET NOT NULL;

ALTER TABLE gn2pg_import.error_log
    DROP COLUMN id_data;

DROP TABLE gn2pg_import.download_log;
DROP TABLE gn2pg_import.increment_log;

COMMIT;
```

## 1.8.1 - 2025-04-18

### :bug: Fixes

- Fix wrongly deleted IF condition

### :point_down: Release note

To do for update (only)

- Update the app

```bash
pip install --upgrade gn2pg-client
```

- Add a unique constraint on data_json.uuid table (if not already added after upgrade to 1.8.0):

```sql
BEGIN;
ALTER TABLE ONLY gn2pg_import.data_json
    ADD CONSTRAINT unique_uuid UNIQUE (uuid);
COMMIT;
```

- For users who use `GN2PG_client` to populate a GeoNature database, update SQL triggers.

```bash
gn2pg_cli db --custom-script=to_gnsynthese myconfig.toml
```


## 1.8.0 - 2025-04-18

### :rocket: New features

- :point_right: Restructure command line commands into 3 sub-commands :
    - `gn2pg_cli config`: Configuration management
    - `gn2pg_cli db`: Receiver database management
    - `gn2pg_cli download`: Download management
- Add config commands to list/read/edit configuration files stored in `~/.gn2pg` directory, execute `gn2pg_cli config --help` for more informations.
- File log output and stdout are now the same (fix #109).
- Implement requests Retry on http 50x errors (fix #113, #108).
- Move on to the next source after a failed download from a source. In the event of failure, the next update will resume at the last successful run.
- The data integration process in GeoNature now uses the UUID as the data identifier (fix #112).

### :gift: Other changes

- Documentation update (now using [Sphinx press theme](https://github.com/schettino72/sphinx_press_theme)).
- Code cleanup.
- Complete translations.

### :point_down: Release note

To do for update (only)

- Update the app

```bash
pip install --upgrade gn2pg-client
```

- Add a unique constraint on data_json.uuid table (if not already added after upgrade to 1.8.0):

```sql
BEGIN;
ALTER TABLE ONLY gn2pg_import.data_json
    ADD CONSTRAINT unique_uuid UNIQUE (uuid);
COMMIT;
```

- For users who use `GN2PG_client` to populate a GeoNature database, update SQL triggers.

```bash
gn2pg_cli db --custom-script=to_gnsynthese myconfig.toml
```

## 1.7.0 - 2025-02-24

### Fixes

- Quick fix for #103, pending a better fix to exclude metadata insertions for rejected data, partially fix #103.
- Various little fixes

## 1.6.9 - 2024-10-08

### Fixes

- TypeError while using new importlib resources, fix #94

## 1.6.8 - 2024-10-08 (unpublished)

...

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
