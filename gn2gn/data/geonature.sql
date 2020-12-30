/*
 SQL Scripts to automate populate of a GeoNature database from imported data

 Import steps when UPSERT data are:
   1. get or create Acquisition Framework (from Acquisition Framework UUID)
   2. get or create Dataset (from Dataset UUID)
   3. insert or update synthese data (from source/id_synthese, UUID may be NULL...)

 */

/* Acquisition Frameworks */



DROP FUNCTION IF EXISTS gn2gn_import.fct_c_get_or_insert_basic_af_from_uuid_name(_uuid UUID, _name TEXT);

CREATE OR REPLACE FUNCTION gn2gn_import.fct_c_get_or_insert_basic_af_from_uuid_name(_uuid UUID, _name TEXT) RETURNS INTEGER
AS
$$
DECLARE
    the_af_id INT ;
BEGIN
    insert into
        gn_meta.t_acquisition_frameworks ( unique_acquisition_framework_id, acquisition_framework_name
                                         , acquisition_framework_desc, acquisition_framework_start_date)
    select _uuid, _name, 'Description of acquisition framework : ' || _name, now()
    where
        not exists(
                select 1
                from
                    gn_meta.t_acquisition_frameworks
                where unique_acquisition_framework_id = _uuid
            );
    SELECT id_acquisition_framework
    into the_af_id
    FROM gn_meta.t_acquisition_frameworks
    WHERE unique_acquisition_framework_id = _uuid;

    RETURN the_af_id;
END
$$
    LANGUAGE plpgsql;


COMMENT ON FUNCTION gn2gn_import.fct_c_get_or_insert_basic_af_from_uuid_name(_uuid UUID, _name TEXT) IS 'function to basically create acquisition framework';

/* Datasets */
DROP FUNCTION IF EXISTS gn2gn_import.fct_c_get_or_insert_basic_dataset_from_uuid_name(_uuid UUID, _name TEXT, _id_af INT);

CREATE OR REPLACE FUNCTION gn2gn_import.fct_c_get_or_insert_basic_dataset_from_uuid_name(_uuid UUID, _name TEXT, _id_af INT) RETURNS INTEGER
AS
$$
DECLARE
    the_dataset_id INT ;
BEGIN
    INSERT INTO
        gn_meta.t_datasets( id_acquisition_framework
                          , dataset_name
                          , dataset_shortname
                          , dataset_desc
                          , marine_domain
                          , terrestrial_domain
                          , meta_create_date)
    SELECT
        _id_af
      , _name
      , left(_name, 30)
      , 'A compléter'
      , TRUE
      , TRUE
      , now()
    where
        not exists(
                select 1
                from
                    gn_meta.t_datasets
                where unique_dataset_id = _uuid
            );
    SELECT id_dataset
    into the_dataset_id
    FROM gn_meta.t_datasets
    WHERE unique_dataset_id = _uuid;

    RETURN the_dataset_id;
END
$$
    LANGUAGE plpgsql;


COMMENT ON FUNCTION gn2gn_import.fct_c_get_or_insert_basic_dataset_from_uuid_name(_uuid UUID, _name TEXT, _id_af INT) IS 'function to basically create acquisition framework';

/* Sources */


DROP FUNCTION IF EXISTS gn2gn_import.fct_c_get_or_insert_source(_source TEXT);

CREATE OR REPLACE FUNCTION gn2gn_import.fct_c_get_or_insert_source(_source TEXT) RETURNS INTEGER
AS
$$
DECLARE
    the_source_id INT ;
BEGIN
    INSERT INTO
        gn_synthese.t_sources(name_source)
    SELECT
        _source
    where
        not exists(
                select 1
                from
                    gn_synthese.t_sources
                where name_source = _source
            );
    SELECT id_source
    into the_source_id
    FROM gn_synthese.t_sources
    WHERE name_source = _source;

    RETURN the_source_id;
END
$$
    LANGUAGE plpgsql;


COMMENT ON FUNCTION gn2gn_import.fct_c_get_or_insert_source(_source TEXT) IS 'function to basically create new sources';

/* UPSERT INTO Synthese */

