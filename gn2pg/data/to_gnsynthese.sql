/*
 SQL Scripts to automate populate of a GeoNature database from imported data

 Before to start, please adapt the name of the schema 'gn2pg_import' to the one you set in your config file.
 You can run either all the script at once of do it manually (without the first Begin line).
 Indeed, you might have problem with the following line if you have duplicated data in your GeoNature synthesis:
 'CREATE UNIQUE INDEX IF NOT EXISTS uidx_synthese_id_source_id_entity_source_pk_value ON gn_synthese.synthese (id_source, entity_source_pk_value);'
 To check if you have duplicates (and delete them if wanted), see : https://github.com/PnX-SI/GeoNature/commit/02b704f1898abc8ae7820e6b3d42f7840f3c971a

 Import steps when UPSERT data are:
 1. get or create Acquisition Framework (from Acquisition Framework UUID)
 2. get or create Dataset (from Dataset UUID)
 3. insert or update synthese data (from source/id_synthese, UUID may be NULL...)
 */
/* Acquisition Frameworks */
BEGIN;

CREATE SCHEMA IF NOT EXISTS gn2pg_import;

DROP FUNCTION IF EXISTS
    gn2pg_import.fct_c_get_or_insert_basic_af_from_uuid_name (_uuid uuid,
                                                              _name TEXT);

CREATE OR REPLACE FUNCTION
    gn2pg_import.fct_c_check_has_additional_data_column(_schema_name VARCHAR, _table_name VARCHAR, _column_name VARCHAR)
    RETURNS bool
AS
$func$
DECLARE
    the_has_column bool;
BEGIN
    SELECT EXISTS (SELECT 1
                   FROM information_schema.columns
                   WHERE table_schema = _schema_name
                     AND table_name = _table_name
                     AND column_name = _column_name)
    INTO the_has_column;
    RETURN the_has_column;
END;
$func$
    LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION
    gn2pg_import.fct_c_get_or_insert_basic_af_from_uuid_name(_uuid uuid,
                                                             _name TEXT)
    RETURNS INTEGER
AS
$func$
DECLARE
    the_af_id INT;
BEGIN
    IF NOT EXISTS (SELECT 1
                   FROM gn_meta.t_acquisition_frameworks
                   WHERE unique_acquisition_framework_id = _uuid)
    THEN
        INSERT INTO gn_meta.t_acquisition_frameworks
        (unique_acquisition_framework_id, acquisition_framework_name,
         acquisition_framework_desc, acquisition_framework_start_date,
         meta_create_date)
        SELECT _uuid
             , _name
             , 'Description of acquisition framework : ' || _name
             , NOW()
             , NOW()
        RETURNING id_acquisition_framework INTO the_af_id;

        IF gn2pg_import.fct_c_check_has_additional_data_column('gn_meta', 't_acquisition_frameworks', 'additional_data')
        THEN
            UPDATE gn_meta.t_acquisition_frameworks
            SET additional_data = JSONB_SET(
                    JSONB_SET(additional_data, '{source}', TO_JSONB(_name), TRUE)
                , '{module}', '"gn2pg"'::jsonb, TRUE)
            WHERE id_acquisition_framework = the_af_id;
        END IF;
    ELSE
        SELECT id_acquisition_framework
        INTO the_af_id
        FROM gn_meta.t_acquisition_frameworks
        WHERE unique_acquisition_framework_id = _uuid;
    END IF;
    RETURN the_af_id;
END
$func$
    LANGUAGE plpgsql;

COMMENT ON FUNCTION gn2pg_import.fct_c_get_or_insert_basic_af_from_uuid_name
    (_uuid uuid , _name TEXT) IS 'function to basically create acquisition framework';


/* Datasets */
DROP FUNCTION IF EXISTS
    gn2pg_import.fct_c_get_or_insert_basic_dataset_from_uuid_name (_uuid uuid,
                                                                   _name TEXT, _id_af INT);

CREATE OR REPLACE FUNCTION
    gn2pg_import.fct_c_get_or_insert_basic_dataset_from_uuid_name(_uuid uuid,
                                                                  _name TEXT, _id_af INT)
    RETURNS INTEGER
AS
$func$
DECLARE
    the_dataset_id INT;
BEGIN
    IF NOT EXISTS (SELECT 1
                   FROM gn_meta.t_datasets
                   WHERE unique_dataset_id = _uuid)
    THEN
        INSERT INTO gn_meta.t_datasets (unique_dataset_id,
                                        id_acquisition_framework, dataset_name, dataset_shortname,
                                        dataset_desc, marine_domain, terrestrial_domain, meta_create_date)
        SELECT _uuid
             , _id_af
             , _name
             , LEFT(_name
            , 30)
             , 'A compléter'
             , TRUE
             , TRUE
             , NOW()
        RETURNING id_dataset INTO the_dataset_id;

        IF gn2pg_import.fct_c_check_has_additional_data_column(
                'gn_meta',
                't_datasets',
                'additional_data'
           )
        THEN
            UPDATE gn_meta.t_datasets
            SET additional_data = JSONB_SET(
                    JSONB_SET(additional_data, '{source}', TO_JSONB(_name), TRUE)
                , '{module}', '"gn2pg"'::jsonb, TRUE)
            WHERE id_dataset = the_dataset_id;
        END IF;
    ELSE
        SELECT id_dataset
        INTO the_dataset_id
        FROM gn_meta.t_datasets
        WHERE unique_dataset_id = _uuid;
    END IF;
    RETURN the_dataset_id;
END
$func$
    LANGUAGE plpgsql;

COMMENT ON FUNCTION
    gn2pg_import.fct_c_get_or_insert_basic_dataset_from_uuid_name (_uuid uuid ,
    _name TEXT , _id_af INT) IS 'function to basically create datasets';


/* Sources */
DROP FUNCTION IF EXISTS gn2pg_import.fct_c_get_or_insert_source (_source TEXT);

CREATE OR REPLACE FUNCTION gn2pg_import.fct_c_get_or_insert_source(_source TEXT)
    RETURNS INTEGER
AS
$func$
DECLARE
    the_source_id INT;
BEGIN
    IF NOT EXISTS (SELECT 1
                   FROM gn_synthese.t_sources
                   WHERE name_source = _source)
    THEN
        INSERT INTO gn_synthese.t_sources (name_source)
        SELECT _source
        RETURNING id_source INTO the_source_id;

        IF gn2pg_import.fct_c_check_has_additional_data_column(
                'gn_synthese',
                't_sources',
                'additional_data'
           )
        THEN
            UPDATE gn_synthese.t_sources
            SET additional_data = JSONB_SET(
                    JSONB_SET(additional_data, '{source}', TO_JSONB(_source), TRUE)
                , '{module}', '"gn2pg"'::jsonb, TRUE)
            WHERE id_source = the_source_id;
        END IF;
    ELSE
        SELECT id_source
        INTO the_source_id
        FROM gn_synthese.t_sources
        WHERE name_source = _source;
    END IF;
    RETURN the_source_id;
END
$func$
    LANGUAGE plpgsql;

COMMENT ON FUNCTION gn2pg_import.fct_c_get_or_insert_source (_source TEXT) IS
    'function to basically create new sources';


/*  Nomenclatures */
DROP FUNCTION IF EXISTS gn2pg_import.fct_c_get_id_nomenclature_from_label
    (_type TEXT, _label TEXT);

CREATE OR REPLACE FUNCTION gn2pg_import.fct_c_get_id_nomenclature_from_label(_type TEXT, _label TEXT)
    RETURNS INTEGER
AS
$func$
DECLARE
    the_id_nomenclature INT;
BEGIN
    SELECT id_nomenclature
    INTO the_id_nomenclature
    FROM ref_nomenclatures.t_nomenclatures n
             JOIN ref_nomenclatures.bib_nomenclatures_types t ON n.id_type = t.id_type
    WHERE t.mnemonique LIKE _type
      AND n.label_default = _label;
    RETURN the_id_nomenclature;
END
$func$
    LANGUAGE plpgsql;

COMMENT ON FUNCTION gn2pg_import.fct_c_get_id_nomenclature_from_label (_type
    TEXT , _label TEXT) IS 'function to retrieve nomenclature ID from label';


/* Add unique constraint to synthese on  id_source and /entity_source_pk_value */
CREATE UNIQUE INDEX IF NOT EXISTS
    uidx_synthese_id_source_id_entity_source_pk_value ON gn_synthese.synthese
    (id_source, entity_source_pk_value);

DROP FUNCTION IF EXISTS gn2pg_import.fct_c_insert_af_territories (_id_af
                                                                      INTEGER, _territories jsonb);

CREATE OR REPLACE FUNCTION gn2pg_import.fct_c_insert_af_territories(_id_af
                                                                        INTEGER, _territories jsonb)
    RETURNS BOOLEAN
    LANGUAGE plpgsql
AS
$$
DECLARE
    i RECORD;
BEGIN
    RAISE DEBUG '_id_af %, territories %' , _id_af::INT , _territories;

    FOR i IN (SELECT JSONB_ARRAY_ELEMENTS_TEXT(_territories) item)
        LOOP
            RAISE DEBUG 'iterritory % %' , i , i.item;
            INSERT INTO gn_meta.cor_acquisition_framework_territory
                (id_acquisition_framework, id_nomenclature_territory)
            VALUES (_id_af, ref_nomenclatures.get_id_nomenclature('TERRITOIRE', i.item))
            ON CONFLICT
                DO NOTHING;
        END LOOP;
    RETURN TRUE;
END
$$;

DROP FUNCTION IF EXISTS gn2pg_import.fct_c_insert_af_objectives (_id_af INTEGER
, _objectives jsonb);

CREATE OR REPLACE FUNCTION gn2pg_import.fct_c_insert_af_objectives(_id_af
                                                                       INTEGER, _objectives jsonb)
    RETURNS BOOLEAN
    LANGUAGE plpgsql
AS
$$
DECLARE
    i RECORD;
BEGIN
    RAISE DEBUG '_id_af %, objectives %' , _id_af::INT , _objectives;

    FOR i IN (SELECT JSONB_ARRAY_ELEMENTS_TEXT(_objectives) item)
        LOOP
            RAISE DEBUG 'iterritory % %' , i , i.item;
            INSERT INTO gn_meta.cor_acquisition_framework_objectif
                (id_acquisition_framework, id_nomenclature_objectif)
            VALUES (_id_af, ref_nomenclatures.get_id_nomenclature('CA_OBJECTIFS', i.item))
            ON CONFLICT
                DO NOTHING;
        END LOOP;
    RETURN TRUE;
END
$$;

DROP FUNCTION IF EXISTS gn2pg_import.fct_c_insert_af_sinp_theme (_id_af INTEGER
, _sinp_themes jsonb);

CREATE OR REPLACE FUNCTION gn2pg_import.fct_c_insert_af_sinp_theme(_id_af
                                                                       INTEGER, _sinp_themes jsonb)
    RETURNS BOOLEAN
    LANGUAGE plpgsql
AS
$$
DECLARE
    i RECORD;
BEGIN
    RAISE DEBUG '_id_af %, themes %' , _id_af::INT , _sinp_themes;

    FOR i IN (SELECT JSONB_ARRAY_ELEMENTS_TEXT(_sinp_themes) item)
        LOOP
            RAISE DEBUG 'ithemes % %' , i , i.item;
            INSERT INTO gn_meta.cor_acquisition_framework_voletsinp
                (id_acquisition_framework, id_nomenclature_voletsinp)
            VALUES (_id_af, ref_nomenclatures.get_id_nomenclature('VOLET_SINP', i.item))
            ON CONFLICT
                DO NOTHING;
        END LOOP;
    RETURN TRUE;
END
$$;

DROP FUNCTION IF EXISTS gn2pg_import.fct_c_insert_af_publications (_id_af
                                                                       INTEGER, _objectives jsonb);

CREATE OR REPLACE FUNCTION gn2pg_import.fct_c_insert_af_publications(_id_af
                                                                         INTEGER, _publications jsonb)
    RETURNS VOID
    LANGUAGE plpgsql
AS
$$
DECLARE
    i RECORD;
BEGIN
    RAISE DEBUG '_id_af %, territories %' , _id_af::INT , _objectives;

    FOR i IN (SELECT JSONB_ARRAY_ELEMENTS_TEXT(_objectives) item)
        LOOP
            RAISE DEBUG 'iterritory % %' , i , i.item;
            INSERT INTO gn_meta.sinp_datatype_publications
                (id_acquisition_framework, id_publication)
            VALUES (_id_af, ref_nomenclatures.get_id_nomenclature('CA_OBJECTIFS', i.item))
            ON CONFLICT
                DO NOTHING;
        END LOOP;
END
$$;

DROP FUNCTION IF EXISTS gn2pg_import.fct_c_insert_ds_territories (_id_ds
                                                                      INTEGER, _territories jsonb);

CREATE OR REPLACE FUNCTION gn2pg_import.fct_c_insert_ds_territories(_id_ds
                                                                        INTEGER, _territories jsonb)
    RETURNS VOID
    LANGUAGE plpgsql
AS
$$
DECLARE
    i RECORD;
BEGIN
    RAISE DEBUG '_id_ds %, territories %' , _id_ds::INT , _territories;

    FOR i IN (SELECT JSONB_ARRAY_ELEMENTS_TEXT(_territories) item)
        LOOP
            RAISE DEBUG 'iterritory % %' , i , i.item;
            INSERT INTO gn_meta.cor_dataset_territory (id_dataset, id_nomenclature_territory)
            VALUES (_id_ds, ref_nomenclatures.get_id_nomenclature('TERRITOIRE', coalesce(i.item,'METROP')))
            ON CONFLICT
                DO NOTHING;
        END LOOP;
END
$$;

CREATE OR REPLACE FUNCTION gn2pg_import.fct_c_get_or_create_actors_in_usershub(_actor_role jsonb, _source CHARACTER VARYING)
    RETURNS INTEGER
    LANGUAGE plpgsql
AS
$$
DECLARE
    the_id_actor INTEGER;
BEGIN
    RAISE DEBUG '_actor_role %' , _actor_role;
    IF _actor_role ->> 'type_role' = 'organism' THEN
        INSERT INTO utilisateurs.bib_organismes ( uuid_organisme, nom_organisme
                                                , email_organisme, additional_data)
        VALUES ((_actor_role ->> 'uuid_actor')::uuid, _actor_role #>>
                                                      '{identity,organism_name}', _actor_role ->> 'email',
                JSONB_BUILD_OBJECT('source', _source, 'module'
                    , 'gn2pg'))
        ON CONFLICT (uuid_organisme)
            DO NOTHING;
        SELECT id_organisme
        INTO the_id_actor
        FROM utilisateurs.bib_organismes
        WHERE uuid_organisme = (_actor_role ->> 'uuid_actor')::uuid;
    ELSIF _actor_role ->> 'type_role' = 'role' THEN
        INSERT INTO utilisateurs.t_roles (uuid_role, nom_role, prenom_role,
                                          email, champs_addi)
        VALUES ((_actor_role ->> 'uuid_actor')::uuid, _actor_role #>>
                                                      '{identity,first_name}', _actor_role #>> '{identity,last_name}',
                NULL,
                JSONB_BUILD_OBJECT('source', _source, 'module'
                    , 'gn2pg', 'gn2pg_data',
                                   JSONB_BUILD_OBJECT('email', _actor_role ->>
                                                               'email')))
        ON CONFLICT (uuid_role)
            DO NOTHING;
        SELECT id_role
        INTO the_id_actor
        FROM utilisateurs.t_roles
        WHERE uuid_role = (_actor_role ->> 'uuid_actor')::uuid;
    END IF;
    RETURN the_id_actor;
END
$$;

CREATE OR REPLACE FUNCTION gn2pg_import.fct_c_insert_dataset_actor(_id_dataset
                                                                       INTEGER, _actor_roles jsonb,
                                                                   _source CHARACTER VARYING)
    RETURNS VOID
    LANGUAGE plpgsql
AS
$$
DECLARE
    i RECORD;
BEGIN
    FOR i IN (SELECT JSONB_ARRAY_ELEMENTS(_actor_roles) item)
        LOOP
            IF i.item ->> 'type_role' = 'organism' THEN
                INSERT INTO gn_meta.cor_dataset_actor ( id_dataset, id_organism
                                                      , id_nomenclature_actor_role)
                VALUES (_id_dataset,
                        gn2pg_import.fct_c_get_or_create_actors_in_usershub
                        (i.item, _source),
                        ref_nomenclatures.get_id_nomenclature('ROLE_ACTEUR'
                            , i.item ->> 'cd_nomenclature_actor_role'))
                ON CONFLICT
                    DO NOTHING;
            ELSIF i.item ->> 'type_role' = 'role' THEN
                INSERT INTO gn_meta.cor_dataset_actor (id_dataset, id_role,
                                                       id_nomenclature_actor_role)
                VALUES (_id_dataset,
                        gn2pg_import.fct_c_get_or_create_actors_in_usershub
                        (i.item, _source),
                        ref_nomenclatures.get_id_nomenclature('ROLE_ACTEUR'
                            , i.item ->> 'cd_nomenclature_actor_role'))
                ON CONFLICT
                    DO NOTHING;
            END IF;

        END LOOP;
END
$$;

CREATE OR REPLACE FUNCTION gn2pg_import.fct_c_insert_af_actors(_id_af INTEGER
, _actor_roles jsonb, _source CHARACTER VARYING)
    RETURNS VOID
    LANGUAGE plpgsql
AS
$$
DECLARE
    i RECORD;
BEGIN
    RAISE DEBUG '_id_af %' , _id_af::INT;
    FOR i IN (SELECT JSONB_ARRAY_ELEMENTS(_actor_roles) item)
        LOOP
            IF i.item ->> 'type_role' = 'organism' THEN
                INSERT INTO gn_meta.cor_acquisition_framework_actor
                (id_acquisition_framework, id_organism,
                 id_nomenclature_actor_role)
                VALUES (_id_af,
                        gn2pg_import.fct_c_get_or_create_actors_in_usershub
                        (i.item, _source),
                        ref_nomenclatures.get_id_nomenclature('ROLE_ACTEUR'
                            , i.item ->> 'cd_nomenclature_actor_role'))
                ON CONFLICT
                    DO NOTHING;
            ELSIF i.item ->> 'type_role' = 'role' THEN
                INSERT INTO gn_meta.cor_acquisition_framework_actor
                (id_acquisition_framework, id_role,
                 id_nomenclature_actor_role)
                VALUES (_id_af,
                        gn2pg_import.fct_c_get_or_create_actors_in_usershub
                        (i.item, _source),
                        ref_nomenclatures.get_id_nomenclature('ROLE_ACTEUR'
                            , i.item ->> 'cd_nomenclature_actor_role'))
                ON CONFLICT
                    DO NOTHING;
            END IF;
        END LOOP;
END
$$;

CREATE OR REPLACE FUNCTION gn2pg_import.fct_c_get_or_insert_af_from_af_jsondata(_af_data jsonb, _source CHARACTER VARYING)
    RETURNS INTEGER
AS
$func$
DECLARE
    the_af_id       INT;
    the_territories jsonb;
    the_objectives  jsonb;
    the_voletsinp   jsonb;
BEGIN
    IF NOT EXISTS (SELECT 1
                   FROM gn_meta.t_acquisition_frameworks
                   WHERE unique_acquisition_framework_id = (_af_data #>> '{uuid}')::uuid)
    THEN
        INSERT INTO gn_meta.t_acquisition_frameworks
        (unique_acquisition_framework_id, acquisition_framework_name,
         acquisition_framework_desc, acquisition_framework_start_date,
         acquisition_framework_end_date, ecologic_or_geologic_target,
         id_nomenclature_financing_type, id_nomenclature_territorial_level,
         initial_closing_date, target_description
            --                                          , additional_data
            , meta_create_date, meta_update_date)
        SELECT (_af_data #>> '{uuid}')::uuid
             , (_af_data #>> '{name}')::VARCHAR
             , (_af_data #>> '{desc}')::VARCHAR
             , (_af_data #>> '{start_date}')::DATE
             , (_af_data #>> '{end_date}')::DATE
             , (_af_data #>> '{ecologic_or_geologic_target}')::VARCHAR
             , (ref_nomenclatures.get_id_nomenclature('TYPE_FINANCEMENT', _af_data
            #>> '{financing_type}'))::INT
             , (ref_nomenclatures.get_id_nomenclature('NIVEAU_TERRITORIAL', _af_data
            #>> '{territorial_level}'))::INT
             , (_af_data #>> '{initial_closing_date}')::TIMESTAMP
             , (_af_data #>> '{target_description}')::VARCHAR
             , NOW()
             , NOW()
        RETURNING id_acquisition_framework INTO the_af_id;

        PERFORM
            gn2pg_import.fct_c_insert_af_actors(the_af_id, _af_data -> 'actors', _source);

        IF _af_data ->> 'territories' IS NULL THEN
            SELECT ARRAY_TO_JSON(ARRAY ['METROP'])::jsonb INTO the_territories;
        ELSE
            SELECT _af_data -> 'territories' INTO the_territories;
        END IF;
        PERFORM
            gn2pg_import.fct_c_insert_af_territories(the_af_id, the_territories);
        IF _af_data ->> 'objectives' IS NULL THEN
            SELECT ARRAY_TO_JSON(ARRAY ['11'])::jsonb INTO the_objectives;
        ELSE
            SELECT _af_data -> 'objectives' INTO the_objectives;
        END IF;
        IF _af_data ->> 'voletsinp' IS NULL THEN
            SELECT ARRAY_TO_JSON(ARRAY ['1'])::jsonb INTO the_voletsinp;
        ELSE
            SELECT _af_data -> 'voletsinp' INTO the_voletsinp;
        END IF;

        PERFORM
            gn2pg_import.fct_c_insert_af_territories(the_af_id, the_territories);
        PERFORM
            gn2pg_import.fct_c_insert_af_objectives(the_af_id, the_objectives);
        PERFORM
            gn2pg_import.fct_c_insert_af_sinp_theme(the_af_id, the_voletsinp);

        IF gn2pg_import.fct_c_check_has_additional_data_column(
                'gn_meta',
                't_acquisition_frameworks',
                'additional_data'
           )
        THEN
            UPDATE gn_meta.t_acquisition_frameworks
            SET additional_data = JSONB_SET(
                    JSONB_SET(additional_data, '{source}', TO_JSONB(_source), TRUE)
                , '{module}', '"gn2pg"'::jsonb, TRUE)
            WHERE id_acquisition_framework = the_af_id;
        END IF;
        RETURN the_af_id;
    ELSE
        SELECT id_acquisition_framework
        INTO the_af_id
        FROM gn_meta.t_acquisition_frameworks
        WHERE unique_acquisition_framework_id = (_af_data #>> '{uuid}')::uuid;
    END IF;
    RETURN the_af_id;
END
$func$ LANGUAGE plpgsql;

COMMENT ON FUNCTION gn2pg_import.fct_c_get_or_insert_af_from_af_jsondata (jsonb
    , VARCHAR) IS 'function to create acquisition framework from json structured data';

CREATE OR REPLACE FUNCTION
    gn2pg_import.fct_c_get_or_insert_dataset_from_jsondata(_ds_data jsonb,
                                                           _id_af INTEGER, _source CHARACTER VARYING)
    RETURNS INTEGER
AS
$func$
DECLARE
    the_dataset_id INT;


BEGIN
    IF NOT EXISTS (SELECT 1
                   FROM gn_meta.t_datasets
                   WHERE unique_dataset_id = (_ds_data #>> '{uuid}')::uuid)
    THEN
        INSERT INTO gn_meta.t_datasets (unique_dataset_id,
                                        id_acquisition_framework, dataset_name, dataset_shortname,
                                        dataset_desc, marine_domain, terrestrial_domain,
                                        id_nomenclature_source_status, id_nomenclature_resource_type,
                                        id_nomenclature_dataset_objectif, id_nomenclature_data_origin,
                                        id_nomenclature_collecting_method, id_nomenclature_data_type,
            --                            , additional_data
                                        keywords, meta_create_date, meta_update_date)
        SELECT (_ds_data #>> '{uuid}')::uuid
             , _id_af
             , (_ds_data #>> '{name}')::VARCHAR
             , (_ds_data #>> '{shortname}')::VARCHAR
             , COALESCE((_ds_data #>> '{desc}')::VARCHAR, '...')
             , COALESCE((_ds_data #>> '{marine_domain}')::bool, FALSE)
             , COALESCE((_ds_data #>> '{terrestrial_domain}')::bool, FALSE)
             , (ref_nomenclatures.get_id_nomenclature('STATUT_SOURCE', _ds_data
            #>> '{source_status}'))::INT
             , (ref_nomenclatures.get_id_nomenclature('RESOURCE_TYP', _ds_data
            #>> '{resource_type}'))::INT
             , (ref_nomenclatures.get_id_nomenclature('JDD_OBJECTIFS', _ds_data
            #>> '{dataset_objectif}'))::INT
             , (ref_nomenclatures.get_id_nomenclature('DS_PUBLIQUE', _ds_data
            #>> '{data_origin}'))::INT
             , (ref_nomenclatures.get_id_nomenclature('METHO_RECUEIL', _ds_data
            #>> '{collecting_method}'))::INT
             , (ref_nomenclatures.get_id_nomenclature('DATA_TYP', _ds_data
            #>> '{data_type}'))::INT
             , (_ds_data #>> '{keywords}')::VARCHAR
             , NOW()
             , NOW()
        RETURNING id_dataset INTO the_dataset_id;

        PERFORM
            gn2pg_import.fct_c_insert_dataset_actor(the_dataset_id, _ds_data ->
                                                                    'actors', _source);
        IF JSONB_ARRAY_LENGTH(_ds_data -> 'territories') > 0 THEN
            PERFORM
                gn2pg_import.fct_c_insert_ds_territories(the_dataset_id, _ds_data
                    -> 'territories');
        END IF;
        IF gn2pg_import.fct_c_check_has_additional_data_column(
                'gn_meta',
                't_datasets',
                'additional_data'
           )
        THEN
            UPDATE gn_meta.t_datasets
            SET additional_data = JSONB_SET(
                    JSONB_SET(additional_data, '{source}', TO_JSONB(_source), TRUE)
                , '{module}', '"gn2pg"'::jsonb, TRUE)
            WHERE id_dataset = the_dataset_id;
        END IF;
    ELSE
        SELECT id_dataset
        INTO the_dataset_id
        FROM gn_meta.t_datasets
        WHERE unique_dataset_id = (_ds_data #>> '{uuid}')::uuid;
    END IF;
    RETURN the_dataset_id;
END
$func$ LANGUAGE plpgsql;

COMMENT ON FUNCTION gn2pg_import.fct_c_get_or_insert_dataset_from_jsondata
    (jsonb , INTEGER , VARCHAR) IS 'function to basically create datasets';

-- UPSERT
CREATE OR REPLACE FUNCTION gn2pg_import.fct_tri_c_upsert_data_to_geonature()
    RETURNS TRIGGER
    LANGUAGE plpgsql
AS
$$
DECLARE
    _local_srid                              INT;
    the_unique_id_sinp                       uuid;
    the_unique_id_sinp_grp                   uuid;
    the_id_source                            INT;
    the_entity_source_pk_value               INT;
    the_id_af                                INT;
    the_id_dataset                           INT;
    the_id_nomenclature_geo_object_nature    INT;
    the_id_nomenclature_grp_typ              INT;
    the_grp_method                           VARCHAR;
    the_id_nomenclature_obs_technique        INT;
    the_id_nomenclature_bio_status           INT;
    the_id_nomenclature_bio_condition        INT;
    the_id_nomenclature_naturalness          INT;
    the_id_nomenclature_exist_proof          INT;
    the_id_nomenclature_valid_status         INT;
    the_id_nomenclature_diffusion_level      INT;
    the_id_nomenclature_life_stage           INT;
    the_id_nomenclature_sex                  INT;
    the_id_nomenclature_obj_count            INT;
    the_id_nomenclature_type_count           INT;
    the_id_nomenclature_sensitivity          INT;
    the_id_nomenclature_observation_status   INT;
    the_id_nomenclature_blurring             INT;
    the_id_nomenclature_source_status        INT;
    the_id_nomenclature_info_geo_type        INT;
    the_id_nomenclature_behaviour            INT;
    the_id_nomenclature_biogeo_status        INT;
    the_reference_biblio                     VARCHAR;
    the_count_min                            INT;
    the_count_max                            INT;
    the_cd_nom                               INT;
    the_cd_hab                               INT;
    the_nom_cite                             VARCHAR;
    the_meta_v_taxref                        VARCHAR;
    the_sample_number_proof                  TEXT;
    the_digital_proof                        TEXT;
    the_non_digital_proof                    TEXT;
    the_altitude_min                         INT;
    the_altitude_max                         INT;
    the_depth_min                            INT;
    the_depth_max                            INT;
    the_place_name                           VARCHAR;
    _the_geom_4326                           geometry;
    _the_geom_point                          geometry;
    _the_geom_local                          geometry;
    the_precision                            INT;
    the_date_min                             TIMESTAMP;
    the_date_max                             TIMESTAMP;
    the_validator                            VARCHAR;
    the_validation_comment                   TEXT;
    the_observers                            TEXT;
    the_determiner                           TEXT;
    the_id_digitiser                         INT;
    the_id_nomenclature_determination_method INT;
    the_comment_context                      TEXT;
    the_comment_description                  TEXT;
    the_additional_data                      jsonb;
    the_meta_validation_date                 TIMESTAMP;
BEGIN
    SELECT find_srid('gn_synthese', 'synthese', 'the_geom_local')
    INTO _local_srid;
    SELECT new.uuid
    INTO the_unique_id_sinp;
    SELECT CAST(new.item #>> '{id_perm_grp_sinp}' AS uuid)
    INTO the_unique_id_sinp_grp;
    SELECT gn2pg_import.fct_c_get_or_insert_source(new.source)
    INTO the_id_source;
    SELECT new.item #>> '{id_synthese}'
    INTO the_entity_source_pk_value;
    SELECT CASE new.type
               WHEN 'synthese_with_metadata' THEN
                   gn2pg_import.fct_c_get_or_insert_af_from_af_jsondata(new.item #>
                                                                        '{ca_data}', new.source)
               ELSE
                   gn2pg_import.fct_c_get_or_insert_basic_af_from_uuid_name
                   (CAST(new.item #>> '{ca_uuid}' AS uuid), new.item #>>
                                                            '{ca_nom}')
               END AS the_id_af
    INTO the_id_af;
    SELECT CASE new.type
               WHEN 'synthese_with_metadata' THEN
                   gn2pg_import.fct_c_get_or_insert_dataset_from_jsondata(new.item #>
                                                                          '{jdd_data}', the_id_af, new.source)
               ELSE
                   gn2pg_import.fct_c_get_or_insert_basic_dataset_from_uuid_name
                   (CAST(new.item #>> '{jdd_uuid}' AS uuid), new.item #>>
                                                             '{jdd_nom}', the_id_af)
               END AS id_dataset
    INTO the_id_dataset;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('NAT_OBJ_GEO'
                       , new.item #>> '{nature_objet_geo}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('NAT_OBJ_GEO', new.item #>> '{nature_objet_geo}')
               END AS id_nomenclature_geo_object_nature
    INTO the_id_nomenclature_geo_object_nature;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('TYP_GRP'
                       , new.item #>> '{type_regroupement}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('TYP_GRP', new.item #>> '{type_regroupement}')
               END AS id_nomenclature_grp_typ
    INTO the_id_nomenclature_grp_typ;
    SELECT new.item #>> '{methode_regroupement}'
    INTO the_grp_method;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('METH_OBS'
                       , new.item #>> '{technique_obs}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('METH_OBS', new.item #>> '{technique_obs}')
               END AS id_nomenclature_obs_technique
    INTO the_id_nomenclature_obs_technique;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('STATUT_BIO'
                       , new.item #>> '{statut_biologique}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('STATUT_BIO', new.item #>> '{statut_biologique}')
               END AS id_nomenclature_bio_status
    INTO the_id_nomenclature_bio_status;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('ETA_BIO'
                       , new.item #>> '{etat_biologique}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('ETA_BIO', new.item #>> '{etat_biologique}')
               END AS id_nomenclature_bio_condition
    INTO the_id_nomenclature_bio_condition;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('NATURALITE'
                       , new.item #>> '{naturalite}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('NATURALITE', new.item #>> '{naturalite}')
               END AS id_nomenclature_naturalness
    INTO the_id_nomenclature_naturalness;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('PREUVE_EXIST'
                       , new.item #>> '{preuve_existante}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('PREUVE_EXIST', new.item #>> '{preuve_existante}')
               END AS id_nomenclature_exist_proof
    INTO the_id_nomenclature_exist_proof;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('STATUT_VALID'
                       , new.item #>> '{statut_validation}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('STATUT_VALID', new.item #>> '{statut_validation}')
               END AS id_nomenclature_valid_status
    INTO the_id_nomenclature_valid_status;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('NIV_PRECIS'
                       , new.item #>> '{precision_diffusion}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('NIV_PRECIS', new.item #>> '{precision_diffusion}')
               END AS id_nomenclature_diffusion_level
    INTO the_id_nomenclature_diffusion_level;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('STADE_VIE'
                       , new.item #>> '{stade_vie}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('STADE_VIE', new.item #>> '{stade_vie}')
               END AS id_nomenclature_life_stage
    INTO the_id_nomenclature_life_stage;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('SEXE'
                       , new.item #>> '{sexe}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('SEXE', new.item #>> '{sexe}')
               END AS id_nomenclature_sex
    INTO the_id_nomenclature_sex;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('OBJ_DENBR'
                       , new.item #>> '{objet_denombrement}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('OBJ_DENBR', new.item #>> '{objet_denombrement}')
               END AS id_nomenclature_obj_count
    INTO the_id_nomenclature_obj_count;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('TYP_DENBR'
                       , new.item #>> '{type_denombrement}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('TYP_DENBR', new.item #>> '{type_denombrement}')
               END AS id_nomenclature_type_count
    INTO the_id_nomenclature_type_count;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('SENSIBILITE'
                       , new.item #>> '{niveau_sensibilite}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('SENSIBILITE', new.item #>> '{niveau_sensibilite}')
               END AS id_nomenclature_sensitivity
    INTO the_id_nomenclature_sensitivity;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('STATUT_OBS'
                       , new.item #>> '{statut_observation}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('STATUT_OBS', new.item #>> '{statut_observation}')
               END AS id_nomenclature_observation_status
    INTO the_id_nomenclature_observation_status;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('DEE_FLOU'
                       , new.item #>> '{floutage_dee}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('DEE_FLOU', new.item #>> '{floutage_dee}')
               END AS id_nomenclature_blurring
    INTO the_id_nomenclature_blurring;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('STATUT_SOURCE'
                       , new.item #>> '{statut_source}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('STATUT_SOURCE', new.item #>> '{statut_source}')
               END AS id_nomenclature_source_status
    INTO the_id_nomenclature_source_status;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('TYP_INF_GEO'
                       , new.item #>> '{type_info_geo}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('TYP_INF_GEO', new.item #>> '{type_info_geo}')
               END AS id_nomenclature_info_geo_type
    INTO the_id_nomenclature_info_geo_type;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('OCC_COMPORTEMENT'
                       , new.item #>> '{comportement}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('OCC_COMPORTEMENT', new.item #>> '{comportement}')
               END AS id_nomenclature_behaviour
    INTO the_id_nomenclature_behaviour;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('STAT_BIOGEO'
                       , new.item #>> '{statut_biogeo}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('STAT_BIOGEO', new.item #>> '{statut_biogeo}')
               END AS id_nomenclature_biogeo_status
    INTO the_id_nomenclature_biogeo_status;
    SELECT new.item #>> '{reference_biblio}'
    INTO the_reference_biblio;
    SELECT new.item #>> '{nombre_min}'
    INTO the_count_min;
    SELECT new.item #>> '{nombre_max}'
    INTO the_count_max;
    SELECT new.item #>> '{cd_nom}'
    INTO the_cd_nom;
    SELECT new.item #>> '{cd_hab}'
    INTO the_cd_hab;
    SELECT new.item #>> '{nom_cite}'
    INTO the_nom_cite;
    SELECT new.item #>> '{version_taxref}'
    INTO the_meta_v_taxref;
    SELECT new.item #>> '{numero_preuve}'
    INTO the_sample_number_proof;
    SELECT new.item #>> '{preuve_numerique}'
    INTO the_digital_proof;
    SELECT new.item #>> '{preuve_non_numerique}'
    INTO the_non_digital_proof;
    SELECT new.item #>> '{altitude_min}'
    INTO the_altitude_min;
    SELECT new.item #>> '{altitude_max}'
    INTO the_altitude_max;
    SELECT new.item #>> '{profondeur_min}'
    INTO the_depth_min;
    SELECT new.item #>> '{profondeur_max}'
    INTO the_depth_max;
    SELECT new.item #>> '{nom_lieu}'
    INTO the_place_name;
    SELECT st_setsrid(st_geomfromtext(new.item #>> '{wkt_4326}'), 4326)
    INTO _the_geom_4326;
    SELECT st_centroid(_the_geom_4326)
    INTO _the_geom_point;
    SELECT st_transform(_the_geom_4326, _local_srid)
    INTO _the_geom_local;
    SELECT CAST(new.item #>> '{precision}' AS INT)
    INTO the_precision;
    SELECT CAST(new.item #>> '{date_debut}' AS DATE)
    INTO the_date_min;
    SELECT CAST(new.item #>> '{date_fin}' AS DATE)
    INTO the_date_max;
    SELECT new.item #>> '{validateur}'
    INTO the_validator;
    SELECT new.item #>> '{comment_validation}'
    INTO the_validation_comment;
    SELECT new.item #>> '{observateurs}'
    INTO the_observers;
    SELECT new.item #>> '{determinateur}'
    INTO the_determiner;
    SELECT NULL
    INTO the_id_digitiser;
    SELECT CASE new.type
               WHEN 'synthese_with_label' THEN
                   gn2pg_import.fct_c_get_id_nomenclature_from_label('TYPE'
                       , new.item #>> '{label}')
               ELSE
                   ref_nomenclatures.get_id_nomenclature('TYPE', new.item #>> '{label}')
               END AS id_nomenclature_determination_method
    INTO
        the_id_nomenclature_determination_method;
    SELECT new.item #>> '{comment_releve}'
    INTO the_comment_context;
    SELECT new.item #>> '{comment_occurrence}'
    INTO the_comment_description;
    SELECT new.item #> '{donnees_additionnelles}'
    INTO the_additional_data;
    SELECT NULL
    INTO the_meta_validation_date;


    /* Proceed to upsert */
    INSERT INTO gn_synthese.synthese (unique_id_sinp, unique_id_sinp_grp,
                                      id_source, entity_source_pk_value, id_dataset,
                                      id_nomenclature_geo_object_nature, id_nomenclature_grp_typ,
                                      grp_method, id_nomenclature_obs_technique, id_nomenclature_bio_status
        , id_nomenclature_bio_condition, id_nomenclature_naturalness,
                                      id_nomenclature_exist_proof, id_nomenclature_valid_status,
                                      id_nomenclature_diffusion_level, id_nomenclature_life_stage,
                                      id_nomenclature_sex, id_nomenclature_obj_count,
                                      id_nomenclature_type_count, id_nomenclature_sensitivity,
                                      id_nomenclature_observation_status, id_nomenclature_blurring,
                                      id_nomenclature_source_status, id_nomenclature_info_geo_type,
                                      id_nomenclature_behaviour, id_nomenclature_biogeo_status,
                                      reference_biblio, count_min, count_max, cd_nom, cd_hab, nom_cite,
                                      meta_v_taxref, sample_number_proof, digital_proof, non_digital_proof
        , altitude_min, altitude_max, depth_min, depth_max, place_name,
                                      the_geom_4326, the_geom_point, the_geom_local, precision, date_min
        , date_max, validator, validation_comment, observers, determiner,
                                      id_digitiser, id_nomenclature_determination_method, comment_context,
                                      comment_description, additional_data, meta_validation_date,
                                      last_action)
    VALUES (the_unique_id_sinp, the_unique_id_sinp_grp, the_id_source,
            the_entity_source_pk_value, the_id_dataset,
            the_id_nomenclature_geo_object_nature, the_id_nomenclature_grp_typ
               , the_grp_method, the_id_nomenclature_obs_technique,
            the_id_nomenclature_bio_status, the_id_nomenclature_bio_condition
               , the_id_nomenclature_naturalness, the_id_nomenclature_exist_proof
               , the_id_nomenclature_valid_status,
            the_id_nomenclature_diffusion_level,
            the_id_nomenclature_life_stage, the_id_nomenclature_sex,
            the_id_nomenclature_obj_count, the_id_nomenclature_type_count,
            the_id_nomenclature_sensitivity,
            the_id_nomenclature_observation_status,
            the_id_nomenclature_blurring, the_id_nomenclature_source_status,
            the_id_nomenclature_info_geo_type, the_id_nomenclature_behaviour,
            the_id_nomenclature_biogeo_status, the_reference_biblio,
            the_count_min, the_count_max, the_cd_nom, the_cd_hab,
            the_nom_cite, the_meta_v_taxref, the_sample_number_proof,
            the_digital_proof, the_non_digital_proof, the_altitude_min,
            the_altitude_max, the_depth_min, the_depth_max, the_place_name,
            _the_geom_4326, _the_geom_point, _the_geom_local, the_precision
               , the_date_min, the_date_max, the_validator,
            the_validation_comment, the_observers, the_determiner,
            the_id_digitiser, the_id_nomenclature_determination_method,
            the_comment_context, the_comment_description, the_additional_data
               , the_meta_validation_date, 'I')
    ON CONFLICT (id_source , entity_source_pk_value)
        DO UPDATE SET unique_id_sinp                       = the_unique_id_sinp,
                      unique_id_sinp_grp                   =
                          the_unique_id_sinp_grp,
                      id_source                            = the_id_source,
                      entity_source_pk_value               = the_entity_source_pk_value,
                      id_dataset                           = the_id_dataset,
                      id_nomenclature_geo_object_nature
                                                           = the_id_nomenclature_geo_object_nature,
                      id_nomenclature_grp_typ              = the_id_nomenclature_grp_typ,
                      grp_method                           = the_grp_method,
                      id_nomenclature_obs_technique        =
                          the_id_nomenclature_obs_technique,
                      id_nomenclature_bio_status
                                                           = the_id_nomenclature_bio_status,
                      id_nomenclature_bio_condition        =
                          the_id_nomenclature_bio_condition,
                      id_nomenclature_naturalness
                                                           = the_id_nomenclature_naturalness,
                      id_nomenclature_exist_proof
                                                           = the_id_nomenclature_exist_proof,
                      id_nomenclature_valid_status         = the_id_nomenclature_valid_status
            ,
                      id_nomenclature_diffusion_level      =
                          the_id_nomenclature_diffusion_level,
                      id_nomenclature_life_stage           = the_id_nomenclature_life_stage,
                      id_nomenclature_sex                  = the_id_nomenclature_sex,
                      id_nomenclature_obj_count            = the_id_nomenclature_obj_count,
                      id_nomenclature_type_count           = the_id_nomenclature_type_count,
                      id_nomenclature_sensitivity          = the_id_nomenclature_sensitivity,
                      id_nomenclature_observation_status   =
                          the_id_nomenclature_observation_status,
                      id_nomenclature_blurring             = the_id_nomenclature_blurring,
                      id_nomenclature_source_status        =
                          the_id_nomenclature_source_status,
                      id_nomenclature_info_geo_type        =
                          the_id_nomenclature_info_geo_type,
                      id_nomenclature_behaviour            =
                          the_id_nomenclature_behaviour,
                      id_nomenclature_biogeo_status        =
                          the_id_nomenclature_biogeo_status,
                      reference_biblio                     =
                          the_reference_biblio,
                      count_min                            = the_count_min,
                      count_max                            =
                          the_count_max,
                      cd_nom                               = the_cd_nom,
                      cd_hab                               = the_cd_hab,
                      nom_cite                             = the_nom_cite,
                      meta_v_taxref                        = the_meta_v_taxref,
                      sample_number_proof                  = the_sample_number_proof,
                      digital_proof                        =
                          the_digital_proof,
                      non_digital_proof                    = the_non_digital_proof,
                      altitude_min                         = the_altitude_min,
                      altitude_max                         =
                          the_altitude_max,
                      depth_min                            = the_depth_min,
                      depth_max                            =
                          the_depth_max,
                      place_name                           = the_place_name,
                      the_geom_4326                        =
                          _the_geom_4326,
                      the_geom_point                       = _the_geom_point,
                      the_geom_local                       = _the_geom_local,
                      precision                            = the_precision,
                      date_min                             = the_date_min,
                      date_max                             = the_date_max,
                      validator                            =
                          the_validator,
                      validation_comment                   = the_validation_comment,
                      observers                            = the_observers,
                      determiner                           = the_determiner,
                      id_digitiser                         = the_id_digitiser,
                      id_nomenclature_determination_method =
                          the_id_nomenclature_determination_method,
                      comment_context                      =
                          the_comment_context,
                      comment_description                  =
                          the_comment_description,
                      additional_data                      = the_additional_data
            ,
                      meta_validation_date                 = the_meta_validation_date,
                      last_action
                                                           = 'U';
    RETURN new;
END;
$$;

COMMENT ON FUNCTION gn2pg_import.fct_tri_c_upsert_data_to_geonature () IS 'Trigger function to upsert datas from import to synthese';

DROP TRIGGER IF EXISTS tri_c_upsert_data_to_geonature ON gn2pg_import.data_json;

CREATE TRIGGER tri_c_upsert_data_to_geonature
    AFTER INSERT OR UPDATE
    ON gn2pg_import.data_json
    FOR EACH ROW
EXECUTE PROCEDURE gn2pg_import.fct_tri_c_upsert_data_to_geonature();

-- DELETE
CREATE OR REPLACE FUNCTION gn2pg_import.fct_tri_c_delete_data_from_geonature()
    RETURNS TRIGGER
    LANGUAGE plpgsql
AS
$$
BEGIN
    DELETE
    FROM gn_synthese.synthese
    WHERE (old.item #>> '{id_synthese}',
           gn2pg_import.fct_c_get_or_insert_source(old.source)) =
          (synthese.entity_source_pk_value, synthese.id_source);
    IF NOT found THEN
        RETURN NULL;
    END IF;
    RETURN old;
END;
$$;

COMMENT ON FUNCTION gn2pg_import.fct_tri_c_delete_data_from_geonature () IS 'Trigger function to delete datas';

DROP TRIGGER IF EXISTS tri_c_delete_data_from_geonature ON gn2pg_import.data_json;

CREATE TRIGGER tri_c_delete_data_from_geonature
    AFTER DELETE
    ON gn2pg_import.data_json
    FOR EACH ROW
    WHEN (old.type IN ('synthese_with_label', 'synthese_with_cd_nomenclature', 'synthese_with_metadata'))
EXECUTE PROCEDURE gn2pg_import.fct_tri_c_delete_data_from_geonature();

COMMIT;
