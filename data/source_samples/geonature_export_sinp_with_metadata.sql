DROP VIEW IF EXISTS gn_exports.v_synthese_sinp_with_metadata_for_gn2pg;

CREATE VIEW gn_exports.v_synthese_sinp_with_metadata_for_gn2pg AS
WITH af_actors AS (SELECT cafa.id_acquisition_framework,
                          json_build_object('type_role',
                                            CASE
                                                WHEN cafa.id_organism IS NOT NULL THEN 'organism'::TEXT
                                                WHEN cafa.id_role IS NOT NULL THEN 'role'::TEXT
                                                ELSE NULL::TEXT
                                                END, 'uuid_actor', coalesce(borg.uuid_organisme, tro.uuid_role),
                                            'cd_nomenclature_actor_role', tn.cd_nomenclature, 'identity',
                                            CASE
                                                WHEN cafa.id_organism IS NOT NULL
                                                    THEN json_build_object('organism_name', borg.nom_organisme)
                                                WHEN cafa.id_role IS NOT NULL THEN json_build_object('first_name',
                                                                                                     tro.nom_role,
                                                                                                     'last_name',
                                                                                                     tro.prenom_role) END,
                                            'email', coalesce(borg.email_organisme, tro.email)) AS json_data
                   FROM gn_meta.cor_acquisition_framework_actor cafa
                            LEFT JOIN utilisateurs.bib_organismes borg ON cafa.id_organism = borg.id_organisme
                            LEFT JOIN utilisateurs.t_roles tro ON cafa.id_role = tro.id_role
                            JOIN ref_nomenclatures.t_nomenclatures tn
                                 ON cafa.id_nomenclature_actor_role = tn.id_nomenclature),
     af_territories AS (SELECT caft.id_acquisition_framework,
                               array_agg(DISTINCT t_nomenclatures.cd_nomenclature) AS territories
                        FROM gn_meta.cor_acquisition_framework_territory caft
                                 LEFT JOIN ref_nomenclatures.t_nomenclatures
                                           ON caft.id_nomenclature_territory =
                                              t_nomenclatures.id_nomenclature
                        GROUP BY caft.id_acquisition_framework),
     af_objectives AS (SELECT cafo.id_acquisition_framework,
                              array_agg(DISTINCT t_nomenclatures.cd_nomenclature) AS objectives
                       FROM gn_meta.cor_acquisition_framework_objectif cafo
                                LEFT JOIN ref_nomenclatures.t_nomenclatures
                                          ON cafo.id_nomenclature_objectif =
                                             t_nomenclatures.id_nomenclature
                       GROUP BY cafo.id_acquisition_framework),
     af_voletsinp AS (SELECT cafv.id_acquisition_framework,
                             array_agg(DISTINCT t_nomenclatures.cd_nomenclature) AS voletsinp
                      FROM gn_meta.cor_acquisition_framework_voletsinp cafv
                               LEFT JOIN ref_nomenclatures.t_nomenclatures
                                         ON cafv.id_nomenclature_voletsinp =
                                            t_nomenclatures.id_nomenclature
                      GROUP BY cafv.id_acquisition_framework),
     af_publication AS (SELECT cafp.id_acquisition_framework,
                               array_agg(DISTINCT
                                         jsonb_build_object('uuid', sinp_datatype_publications.unique_publication_id,
                                                            'reference',
                                                            sinp_datatype_publications.publication_reference,
                                                            'url',
                                                            sinp_datatype_publications.publication_url)) AS publications
                        FROM gn_meta.cor_acquisition_framework_publication cafp
                                 LEFT JOIN gn_meta.sinp_datatype_publications
                                           ON cafp.id_publication = sinp_datatype_publications.id_publication
                        GROUP BY cafp.id_acquisition_framework)
--      ,
--      af AS
         (SELECT taf.id_acquisition_framework,
                   jsonb_pretty(jsonb_build_object('uuid', taf.unique_acquisition_framework_id, 'name',
                                      taf.acquisition_framework_name,
                                      'desc', taf.acquisition_framework_desc, 'start_date',
                                      taf.acquisition_framework_start_date, 'end_date',
                                      taf.acquisition_framework_end_date,
                                      'initial_closing_date', taf.initial_closing_date, 'territories',
                                      af_territories.territories, 'territorial_level',
                                      ntl.cd_nomenclature, 'territory_desc', taf.territory_desc, 'objectives',
                                      af_objectives.objectives, 'publications', af_publication.publications,
                                      'financing_type', nft.cd_nomenclature,
                                      'target_description',
                                      taf.target_description, 'ecologic_or_geologic_target',
                                      taf.ecologic_or_geologic_target, 'actors',
                                      json_agg(af_actors.json_data), 'is_parent', taf.is_parent, 'parent_uuid',
                                      tafp.unique_acquisition_framework_id)) AS af_data
            FROM gn_meta.t_acquisition_frameworks taf
                     LEFT JOIN gn_meta.t_acquisition_frameworks tafp
                               ON tafp.id_acquisition_framework = taf.acquisition_framework_parent_id
                     JOIN af_actors ON af_actors.id_acquisition_framework = taf.id_acquisition_framework
                     LEFT JOIN ref_nomenclatures.t_nomenclatures ntl
                               ON taf.id_nomenclature_territorial_level = ntl.id_nomenclature
                     LEFT JOIN ref_nomenclatures.t_nomenclatures nft
                               ON taf.id_nomenclature_financing_type = nft.id_nomenclature
                     LEFT JOIN af_territories ON af_territories.id_acquisition_framework = taf.id_acquisition_framework
                     LEFT JOIN af_objectives ON af_objectives.id_acquisition_framework = taf.id_acquisition_framework
                     LEFT JOIN af_voletsinp ON af_voletsinp.id_acquisition_framework = taf.id_acquisition_framework
                     LEFT JOIN af_publication ON af_publication.id_acquisition_framework = taf.id_acquisition_framework
            GROUP BY taf.id_acquisition_framework, taf.acquisition_framework_name, taf.acquisition_framework_desc,
                     taf.acquisition_framework_start_date, taf.acquisition_framework_end_date, taf.initial_closing_date,
                     ntl.cd_nomenclature, nft.cd_nomenclature, af_territories.territories, af_objectives.objectives,
                     af_voletsinp.voletsinp, af_publication.publications, taf.is_parent,tafp.unique_acquisition_framework_id),
     ds_actors AS (SELECT cda.id_dataset,
                          json_build_object('type_role',
                                            CASE
                                                WHEN cda.id_organism IS NOT NULL THEN 'organism'::TEXT
                                                WHEN cda.id_role IS NOT NULL THEN 'role'::TEXT
                                                ELSE NULL::TEXT
                                                END, 'uuid_actor', coalesce(borg.uuid_organisme, tro.uuid_role),
                                            'cd_nomenclature_actor_role', tn.cd_nomenclature, 'identity',
                                            CASE
                                                WHEN cda.id_organism IS NOT NULL
                                                    THEN json_build_object('organism_name', borg.nom_organisme)
                                                WHEN cda.id_role IS NOT NULL THEN json_build_object('first_name',
                                                                                                    tro.nom_role,
                                                                                                    'last_name',
                                                                                                    tro.prenom_role) END,
                                            'email', coalesce(borg.email_organisme, tro.email)) AS json_data
                   FROM gn_meta.cor_dataset_actor cda
                            LEFT JOIN utilisateurs.bib_organismes borg ON cda.id_organism = borg.id_organisme
                            LEFT JOIN utilisateurs.t_roles tro ON cda.id_role = tro.id_role
                            JOIN ref_nomenclatures.t_nomenclatures tn
                                 ON cda.id_nomenclature_actor_role = tn.id_nomenclature),
     ds AS (SELECT tds.id_dataset,
                   tds.id_acquisition_framework,
                   --    tds.additional_data,
                   jsonb_build_object('uuid', tds.unique_dataset_id, 'name', tds.dataset_name, 'desc', tds.dataset_desc,
                                      'shortname', tds.dataset_shortname, 'data_type', ndt.cd_nomenclature,
                                      'collecting_method', ncm.cd_nomenclature, 'data_origin', ndo.cd_nomenclature,
                                      'dataset_objectif', ndso.cd_nomenclature, 'resource_type', nrt.cd_nomenclature,
                                      'source_status', nss.cd_nomenclature, 'territories', array_agg(DISTINCT
                                                                                                     ref_nomenclatures.get_cd_nomenclature(cdt.id_nomenclature_territory)),
                                      'actors', json_agg(ds_actors.json_data)) AS dataset_data
            FROM gn_meta.t_datasets tds
                     JOIN ds_actors ON ds_actors.id_dataset = tds.id_dataset
                     LEFT JOIN gn_meta.cor_dataset_territory cdt ON cdt.id_dataset = tds.id_dataset
                     LEFT JOIN ref_nomenclatures.t_nomenclatures ndt
                               ON tds.id_nomenclature_data_type = ndt.id_nomenclature
                     LEFT JOIN ref_nomenclatures.t_nomenclatures ncm
                               ON tds.id_nomenclature_collecting_method = ncm.id_nomenclature
                     LEFT JOIN ref_nomenclatures.t_nomenclatures ndo
                               ON tds.id_nomenclature_data_origin = ndo.id_nomenclature
                     LEFT JOIN ref_nomenclatures.t_nomenclatures ndso
                               ON tds.id_nomenclature_dataset_objectif = ndso.id_nomenclature
                     LEFT JOIN ref_nomenclatures.t_nomenclatures nrt
                               ON tds.id_nomenclature_resource_type = nrt.id_nomenclature
                     LEFT JOIN ref_nomenclatures.t_nomenclatures nss
                               ON tds.id_nomenclature_source_status = nss.id_nomenclature
            GROUP BY tds.id_dataset, tds.id_acquisition_framework, tds.unique_dataset_id, tds.dataset_name,
                     tds.dataset_desc, tds.dataset_shortname, ndt.cd_nomenclature, ncm.cd_nomenclature,
                     ndo.cd_nomenclature, ndso.cd_nomenclature, nrt.cd_nomenclature, nss.cd_nomenclature)
SELECT s.id_synthese,
       s.entity_source_pk_value                         AS id_source,
       s.unique_id_sinp                                 AS id_perm_sinp,
       s.unique_id_sinp_grp                             AS id_perm_grp_sinp,
       s.date_min                                       AS date_debut,
       s.date_max                                       AS date_fin,
       s.cd_nom,
       s.meta_v_taxref                                  AS version_taxref,
       s.nom_cite,
       s.count_min                                      AS nombre_min,
       s.count_max                                      AS nombre_max,
       s.altitude_min,
       s.altitude_max,
       s.depth_min                                      AS profondeur_min,
       s.depth_max                                      AS profondeur_max,
       s.observers                                      AS observateurs,
       s.determiner                                     AS determinateur,
       s.validator                                      AS validateur,
       s.sample_number_proof                            AS numero_preuve,
       s.digital_proof                                  AS preuve_numerique,
       s.non_digital_proof                              AS preuve_non_numerique,
       s.comment_context                                AS comment_releve,
       s.comment_description                            AS comment_occurrence,
       ds.dataset_data                                  AS jdd_data,
       af.af_data                                       AS ca_data,
       s.reference_biblio,
       s.cd_hab                                         AS code_habitat,
       h.lb_hab_fr                                      AS habitat,
       s.place_name                                     AS nom_lieu,
       s.precision,
       s.additional_data                                AS donnees_additionnelles,
       st_astext(s.the_geom_4326)                       AS wkt_4326,
       n1.cd_nomenclature                               AS nature_objet_geo,
       n2.cd_nomenclature                               AS type_regroupement,
       s.grp_method                                     AS methode_regroupement,
       n3.cd_nomenclature                               AS comportement,
       n4.cd_nomenclature                               AS technique_obs,
       n5.cd_nomenclature                               AS statut_biologique,
       n6.cd_nomenclature                               AS etat_biologique,
       n7.cd_nomenclature                               AS naturalite,
       n8.cd_nomenclature                               AS preuve_existante,
       n9.cd_nomenclature                               AS precision_diffusion,
       n10.cd_nomenclature                              AS stade_vie,
       n11.cd_nomenclature                              AS sexe,
       n12.cd_nomenclature                              AS objet_denombrement,
       n13.cd_nomenclature                              AS type_denombrement,
       n14.cd_nomenclature                              AS niveau_sensibilite,
       n15.cd_nomenclature                              AS statut_observation,
       n16.cd_nomenclature                              AS floutage_dee,
       n17.cd_nomenclature                              AS statut_source,
       n18.cd_nomenclature                              AS type_info_geo,
       n19.cd_nomenclature                              AS methode_determination,
       n20.cd_nomenclature                              AS statut_validation,
       coalesce(s.meta_update_date, s.meta_create_date) AS derniere_action
FROM gn_synthese.synthese s
         JOIN ds ON ds.id_dataset = s.id_dataset
         JOIN af ON ds.id_acquisition_framework = af.id_acquisition_framework
         LEFT JOIN ref_habitats.habref h ON h.cd_hab = s.cd_hab
         LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON s.id_nomenclature_geo_object_nature = n1.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n2 ON s.id_nomenclature_grp_typ = n2.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n3 ON s.id_nomenclature_behaviour = n3.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n4 ON s.id_nomenclature_obs_technique = n4.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n5 ON s.id_nomenclature_bio_status = n5.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n6 ON s.id_nomenclature_bio_condition = n6.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n7 ON s.id_nomenclature_naturalness = n7.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n8 ON s.id_nomenclature_exist_proof = n8.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n9 ON s.id_nomenclature_diffusion_level = n9.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n10 ON s.id_nomenclature_life_stage = n10.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n11 ON s.id_nomenclature_sex = n11.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n12 ON s.id_nomenclature_obj_count = n12.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n13 ON s.id_nomenclature_type_count = n13.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n14 ON s.id_nomenclature_sensitivity = n14.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n15 ON s.id_nomenclature_observation_status = n15.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n16 ON s.id_nomenclature_blurring = n16.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n17 ON s.id_nomenclature_source_status = n17.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n18 ON s.id_nomenclature_info_geo_type = n18.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n19 ON s.id_nomenclature_determination_method = n19.id_nomenclature
         LEFT JOIN ref_nomenclatures.t_nomenclatures n20 ON s.id_nomenclature_valid_status = n20.id_nomenclature
ORDER BY s.id_synthese;
