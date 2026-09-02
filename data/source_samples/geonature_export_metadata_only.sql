/*
 Export mettant à disposition les métadonnées détaillées seulement
 */
BEGIN;

DROP VIEW IF EXISTS gn_exports.v_metadata_only_for_gn2pg;

CREATE VIEW gn_exports.v_metadata_only_for_gn2pg AS
WITH af_ids AS (
    SELECT DISTINCT
        taf.id_acquisition_framework
    FROM
        gn_meta.t_acquisition_frameworks taf
        /* TODO: Adapt to your needs */
        -- JOIN ...
        -- WHERE ...
)
, ds_ids AS (
    SELECT DISTINCT
        tds.id_dataset
        , tds.unique_dataset_id AS jdd_uuid
    FROM
        gn_meta.t_datasets tds
        /* TODO: Adapt to your needs */
        -- JOIN ...
        -- WHERE ...
)
, af_actors AS (
    SELECT
        cafa.id_acquisition_framework
        /* */
        , json_build_object('type_role'
            , CASE WHEN cafa.id_organism IS NOT NULL THEN
                'organism'::TEXT
            WHEN cafa.id_role IS NOT NULL THEN
                'role'::TEXT
            ELSE
                NULL::TEXT
            END
            , 'uuid_actor'
            , coalesce(borg.uuid_organisme
                , tro.uuid_role)
            , 'cd_nomenclature_actor_role'
            , tn.cd_nomenclature
            , 'identity'
            , CASE WHEN cafa.id_organism IS NOT NULL THEN
                json_build_object('organism_name'
                    , borg.nom_organisme)
            WHEN cafa.id_role IS NOT NULL THEN
                json_build_object('first_name'
                    , tro.nom_role
                    , 'last_name'
                    , tro.prenom_role)
            ELSE
                NULL::JSON
            END
            , 'email'
            , coalesce(borg.email_organisme
                , tro.email)) AS json_data
    FROM
        gn_meta.cor_acquisition_framework_actor cafa
        JOIN af_ids ON cafa.id_acquisition_framework = af_ids.id_acquisition_framework
        LEFT JOIN utilisateurs.bib_organismes borg ON cafa.id_organism = borg.id_organisme
        LEFT JOIN utilisateurs.t_roles tro ON cafa.id_role = tro.id_role
	JOIN ref_nomenclatures.t_nomenclatures tn ON
	    cafa.id_nomenclature_actor_role = tn.id_nomenclature
)
, af_territories AS (
    SELECT
        caft.id_acquisition_framework
        , array_agg(DISTINCT t_nomenclatures.cd_nomenclature) AS territories
    FROM
        gn_meta.cor_acquisition_framework_territory caft
        JOIN af_ids ON caft.id_acquisition_framework = af_ids.id_acquisition_framework
	LEFT JOIN ref_nomenclatures.t_nomenclatures ON
	    caft.id_nomenclature_territory = t_nomenclatures.id_nomenclature
    GROUP BY
        caft.id_acquisition_framework
)
, af_objectives AS (
    SELECT
        cafo.id_acquisition_framework
        , array_agg(DISTINCT t_nomenclatures.cd_nomenclature) AS objectives
    FROM
        gn_meta.cor_acquisition_framework_objectif cafo
        JOIN af_ids ON cafo.id_acquisition_framework = af_ids.id_acquisition_framework
	LEFT JOIN ref_nomenclatures.t_nomenclatures ON
	    cafo.id_nomenclature_objectif = t_nomenclatures.id_nomenclature
    GROUP BY
        cafo.id_acquisition_framework
)
, af_voletsinp AS (
    SELECT
        cafv.id_acquisition_framework
        , array_agg(DISTINCT t_nomenclatures.cd_nomenclature) AS voletsinp
    FROM
        gn_meta.cor_acquisition_framework_voletsinp cafv
        JOIN af_ids ON cafv.id_acquisition_framework = af_ids.id_acquisition_framework
	LEFT JOIN ref_nomenclatures.t_nomenclatures ON
	    cafv.id_nomenclature_voletsinp = t_nomenclatures.id_nomenclature
    GROUP BY
        cafv.id_acquisition_framework
)
, af_publication AS (
    SELECT
        cafp.id_acquisition_framework
        , array_agg(DISTINCT jsonb_build_object('uuid'
                , sinp_datatype_publications.unique_publication_id
                , 'reference'
                , sinp_datatype_publications.publication_reference
                , 'url'
                , sinp_datatype_publications.publication_url)) AS publications
    FROM
        gn_meta.cor_acquisition_framework_publication cafp
        JOIN af_ids ON cafp.id_acquisition_framework = af_ids.id_acquisition_framework
	LEFT JOIN gn_meta.sinp_datatype_publications ON cafp.id_publication =
	    sinp_datatype_publications.id_publication
    GROUP BY
        cafp.id_acquisition_framework
)
, af AS (
    SELECT
        taf.id_acquisition_framework
        , taf.unique_acquisition_framework_id AS uuid
        , taf.acquisition_framework_name AS name
        , taf.acquisition_framework_desc AS desc
        , taf.acquisition_framework_start_date AS start_date
        , taf.acquisition_framework_end_date AS end_date
        , taf.initial_closing_date AS initial_closing_date
        , af_territories.territories AS territories
        , ntl.cd_nomenclature AS territorial_level
        , taf.territory_desc AS territory_desc
        , af_objectives.objectives AS objectives
        , af_publication.publications AS publications
        , nft.cd_nomenclature AS financing_type
        , taf.target_description AS target_description
        , taf.ecologic_or_geologic_target AS ecologic_or_geologic_target
        , af_voletsinp.voletsinp AS sinp_theme
        , json_agg(af_actors.json_data) AS actors
        , taf.is_parent AS is_parent
        , tafp.unique_acquisition_framework_id AS parent_uuid
        , taf.meta_update_date AS meta_update_date
    FROM
        gn_meta.t_acquisition_frameworks taf
        JOIN af_ids ON taf.id_acquisition_framework = af_ids.id_acquisition_framework
	LEFT JOIN gn_meta.t_acquisition_frameworks tafp ON
	    tafp.id_acquisition_framework = taf.acquisition_framework_parent_id
        JOIN af_actors ON af_actors.id_acquisition_framework = taf.id_acquisition_framework
	LEFT JOIN ref_nomenclatures.t_nomenclatures ntl ON
	    taf.id_nomenclature_territorial_level = ntl.id_nomenclature
	LEFT JOIN ref_nomenclatures.t_nomenclatures nft ON
	    taf.id_nomenclature_financing_type = nft.id_nomenclature
	LEFT JOIN af_territories ON af_territories.id_acquisition_framework =
	    taf.id_acquisition_framework
	LEFT JOIN af_objectives ON af_objectives.id_acquisition_framework =
	    taf.id_acquisition_framework
	LEFT JOIN af_voletsinp ON af_voletsinp.id_acquisition_framework =
	    taf.id_acquisition_framework
	LEFT JOIN af_publication ON af_publication.id_acquisition_framework =
	    taf.id_acquisition_framework
    GROUP BY
        taf.id_acquisition_framework
        , taf.acquisition_framework_name
        , taf.acquisition_framework_desc
        , taf.acquisition_framework_start_date
        , taf.acquisition_framework_end_date
        , taf.initial_closing_date
        , ntl.cd_nomenclature
        , nft.cd_nomenclature
        , af_territories.territories
        , af_objectives.objectives
        , af_voletsinp.voletsinp
        , af_publication.publications
        , taf.is_parent
        , tafp.unique_acquisition_framework_id
)
, ds_actors AS (
    SELECT
        cda.id_dataset
        , json_build_object('type_role'
            , CASE WHEN cda.id_organism IS NOT NULL THEN
                'organism'::TEXT
            WHEN cda.id_role IS NOT NULL THEN
                'role'::TEXT
            ELSE
                NULL::TEXT
            END
            , 'uuid_actor'
            , coalesce(borg.uuid_organisme
                , tro.uuid_role)
            , 'cd_nomenclature_actor_role'
            , tn.cd_nomenclature
            , 'identity'
            , CASE WHEN cda.id_organism IS NOT NULL THEN
                json_build_object('organism_name'
                    , borg.nom_organisme)
            WHEN cda.id_role IS NOT NULL THEN
                json_build_object('first_name'
                    , tro.nom_role
                    , 'last_name'
                    , tro.prenom_role)
            ELSE
                NULL::JSON
            END
            , 'email'
            , coalesce(borg.email_organisme
                , tro.email)) AS json_data
    FROM
        gn_meta.cor_dataset_actor cda
        JOIN ds_ids ON ds_ids.id_dataset = cda.id_dataset
        LEFT JOIN utilisateurs.bib_organismes borg ON cda.id_organism = borg.id_organisme
        LEFT JOIN utilisateurs.t_roles tro ON cda.id_role = tro.id_role
	JOIN ref_nomenclatures.t_nomenclatures tn ON
	    cda.id_nomenclature_actor_role = tn.id_nomenclature
)
, ds_protocols AS (
    SELECT
        cdp.id_dataset
        , jsonb_build_object('uuid'
            , sdp.unique_protocol_id
            , 'name'
            , sdp.protocol_name
            , 'desc'
            , sdp.protocol_desc
            , 'url'
            , sdp.protocol_url
            , 'type'
            , t_nomenclatures.cd_nomenclature) AS protocols
    FROM
        gn_meta.cor_dataset_protocol cdp
        JOIN ds_ids ON ds_ids.id_dataset = cdp.id_dataset
        JOIN gn_meta.sinp_datatype_protocols sdp ON cdp.id_protocol = sdp.id_protocol
	LEFT JOIN ref_nomenclatures.t_nomenclatures ON
	    sdp.id_nomenclature_protocol_type = t_nomenclatures.id_nomenclature
)
, ds AS (
    SELECT
        tds.id_dataset
        , tds.id_acquisition_framework
        , jsonb_build_object('uuid'
            , tds.unique_dataset_id
            , 'name'
            , tds.dataset_name
            , 'desc'
            , tds.dataset_desc
            , 'shortname'
            , tds.dataset_shortname
            , 'data_type'
            , ndt.cd_nomenclature
            , 'keywords'
            , tds.keywords
            , 'marine_domain'
            , tds.marine_domain
            , 'terrestrial_domain'
            , tds.terrestrial_domain
            , 'collecting_method'
            , ncm.cd_nomenclature
            , 'protocols'
            , ds_protocols.protocols
            , 'data_origin'
            , ndo.cd_nomenclature
            , 'dataset_objectif'
            , ndso.cd_nomenclature
            , 'resource_type'
            , nrt.cd_nomenclature
            , 'source_status'
            , nss.cd_nomenclature
            , 'territories'
	    , array_agg(DISTINCT ref_nomenclatures.get_cd_nomenclature
		(cdt.id_nomenclature_territory))
            , 'actors'
            , json_agg(ds_actors.json_data)) AS dataset_data
        , tds.meta_update_date
    FROM
        gn_meta.t_datasets tds
        JOIN ds_ids ON ds_ids.id_dataset = tds.id_dataset
        JOIN ds_actors ON ds_actors.id_dataset = tds.id_dataset
        LEFT JOIN gn_meta.cor_dataset_territory cdt ON cdt.id_dataset = tds.id_dataset
        LEFT JOIN ds_protocols ON ds_protocols.id_dataset = tds.id_dataset
	LEFT JOIN ref_nomenclatures.t_nomenclatures ndt ON
	    tds.id_nomenclature_data_type = ndt.id_nomenclature
	LEFT JOIN ref_nomenclatures.t_nomenclatures ncm ON
	    tds.id_nomenclature_collecting_method = ncm.id_nomenclature
	LEFT JOIN ref_nomenclatures.t_nomenclatures ndo ON
	    tds.id_nomenclature_data_origin = ndo.id_nomenclature
	LEFT JOIN ref_nomenclatures.t_nomenclatures ndso ON
	    tds.id_nomenclature_dataset_objectif = ndso.id_nomenclature
	LEFT JOIN ref_nomenclatures.t_nomenclatures nrt ON
	    tds.id_nomenclature_resource_type = nrt.id_nomenclature
	LEFT JOIN ref_nomenclatures.t_nomenclatures nss ON
	    tds.id_nomenclature_source_status = nss.id_nomenclature
    GROUP BY
        tds.id_dataset
        , tds.id_acquisition_framework
        , tds.unique_dataset_id
        , tds.dataset_name
        , tds.dataset_desc
        , tds.dataset_shortname
        , ndt.cd_nomenclature
        , ncm.cd_nomenclature
        , ndo.cd_nomenclature
        , ndso.cd_nomenclature
        , nrt.cd_nomenclature
        , nss.cd_nomenclature
        , ds_protocols.protocols
)
, agg_ds AS (
    SELECT
        ds.id_acquisition_framework
        , jsonb_agg(ds.dataset_data) AS datasets
        , max(ds.meta_update_date) AS meta_update_date
    FROM
        ds
    GROUP BY
        ds.id_acquisition_framework
)
SELECT
    af.id_acquisition_framework
    , af.uuid
    , af.name
    , af.desc
    , af.start_date
    , af.end_date
    , af.initial_closing_date
    , af.territories
    , af.territorial_level
    , af.territory_desc
    , af.objectives
    , af.publications
    , af.financing_type
    , af.target_description
    , af.ecologic_or_geologic_target
    , af.sinp_theme
    , af.actors
    , af.is_parent
    , af.parent_uuid
    , agg_ds.datasets AS datasets
    , (
        SELECT
            max(meta_update_date)
        FROM
	    unnest(ARRAY[af.meta_update_date , agg_ds.meta_update_date]) AS
		meta_update_date) AS meta_update_date
FROM
    af
    JOIN agg_ds ON agg_ds.id_acquisition_framework = af.id_acquisition_framework;

COMMIT;
