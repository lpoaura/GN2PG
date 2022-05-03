HowTo
=====

Help
++++

.. code-block:: bash

    gn2pg_cli --help

Init config file
++++++++++++++++

This command init a TOML config file within ``~/.gn2pg`` hidden directory (in user ``HOME`` directory), named as you want. PLEASE DO NOT SPECIFY PATH!

.. code-block:: bash

    gn2pg_cli --init <myconfigfile>


Config file is structured as this. ``[[source]]`` block can be duplicate as many as needed (one block for each source).

.. code-block:: TOML

    # GN2PG configuration file

    # Local db configuration
    [db]
    db_host = "localhost"
    db_port = 5432
    db_user = "<dbUser>"
    db_password = "<dbPassword>"
    db_name = "<dbName>"
    db_schema_import = "schema"
        # Additional connection options (optional)
        [db.db_querystring]
        sslmode = "prefer"


    # Source configuration, 
    # Ducplicate this block for each source (1 source = 1 export)
    [[source]]
    # Source name, will be use to tag stored data in import table
    name = "Source1"
    # GeoNature source login
    user_name = "<monuser>"
    # GeoNature source password
    user_password = "<monPwd>"
    # GeoNature source URL
    url = "<http://geonature1/>"
    # GeoNature source Export id
    export_id = 1
    data_type = "synthese_with_metadata"
    # GeoNature ID application (default is 3)
    id_application = 1
    # Additional export API QueryStrings to filter or order data
    [source.query_strings]
    orderby = 'id_synthese'

    [[source]]
    # Source configuration
    name = "Source2"
    user_name = "<monuser>"
    user_password = "<monPwd>"
    url = "<http://geonature2/>"
    export_id = 1

    # Optional values
    [tuning]
    # page limit length
    max_page_length = 100


.. tip::

   You can add variable in source block ``enable = false`` to disable a source

.. tip::

   Default ``data_type`` (if not defined) is ``synthese_with_cd_nomenclature``, this type is used to conditioning triggers to populate ``gn_synthese.synthese``. This value can be customized for each source with key ``data_type``.
   Provided ``data_type`` are ``synthese_with_label`` for standard GeoNature export, ``synthese_with_cd_nomenclature`` for a standard export using ``cd_nomenclature``, ``synthese_with_metadata`` for and advanced export included metadata

.. tip::

   It is highly recommanded to set and ``orderby`` setting in ``[source.query_strings]`` block (coming soon, actually in development in export module) to order correctly data in export

.. tip::

   You can specify globally page length to download and store data from API (default is 1000) by configuring ``max_page_length`` value in optional ``[tuning]`` block.

 
InitDB Schema and tables
+++++++++++++++++++++++++

To create json tables where datas will be downloaded, run : 

.. code-block:: bash

    gn2pg_cli --json-tables-create <myconfigfile>

.. code-block::

                                                       Table « gn2pg_import.data_json »
    ┌───────────┬─────────────────────────────┬─────────────────┬───────────┬────────────┬──────────┬───────────────────────┬─────────────┐
    │  Colonne  │            Type             │ Collationnement │ NULL-able │ Par défaut │ Stockage │ Cible de statistiques │ Description │
    ├───────────┼─────────────────────────────┼─────────────────┼───────────┼────────────┼──────────┼───────────────────────┼─────────────┤
    │ source    │ character varying           │                 │ not null  │            │ extended │                       │             │
    │ controler │ character varying           │                 │ not null  │            │ extended │                       │             │
    │ type      │ character varying           │                 │ not null  │            │ extended │                       │             │
    │ id_data   │ integer                     │                 │ not null  │            │ plain    │                       │             │
    │ uuid      │ uuid                        │                 │           │            │ plain    │                       │             │
    │ item      │ jsonb                       │                 │ not null  │            │ extended │                       │             │
    │ update_ts │ timestamp without time zone │                 │ not null  │ now()      │ plain    │                       │             │
    └───────────┴─────────────────────────────┴─────────────────┴───────────┴────────────┴──────────┴───────────────────────┴─────────────┘
    Index :
        "pk_source_data" PRIMARY KEY, btree (id_data, source, type)
        "ix_gn2pg_import_data_json_id_data" btree (id_data)
        "ix_gn2pg_import_data_json_uuid" btree (uuid)
    Méthode d'accès : heap

                                            Table « gn2pg_import.datasets_json »
    ┌─────────┬───────────────────┬─────────────────┬───────────┬────────────┬──────────┬───────────────────────┬─────────────┐
    │ Colonne │       Type        │ Collationnement │ NULL-able │ Par défaut │ Stockage │ Cible de statistiques │ Description │
    ├─────────┼───────────────────┼─────────────────┼───────────┼────────────┼──────────┼───────────────────────┼─────────────┤
    │ uuid    │ uuid              │                 │ not null  │            │ plain    │                       │             │
    │ source  │ character varying │                 │ not null  │            │ extended │                       │             │
    │ item    │ jsonb             │                 │ not null  │            │ extended │                       │             │
    └─────────┴───────────────────┴─────────────────┴───────────┴────────────┴──────────┴───────────────────────┴─────────────┘
    Index :
        "meta_json_pk" PRIMARY KEY, btree (uuid, source)
    Méthode d'accès : heap

                                                    Table « gn2pg_import.download_log »
    ┌─────────────┬─────────────────────────────┬─────────────────┬───────────┬────────────┬──────────┬───────────────────────┬─────────────┐
    │   Colonne   │            Type             │ Collationnement │ NULL-able │ Par défaut │ Stockage │ Cible de statistiques │ Description │
    ├─────────────┼─────────────────────────────┼─────────────────┼───────────┼────────────┼──────────┼───────────────────────┼─────────────┤
    │ source      │ character varying           │                 │ not null  │            │ extended │                       │             │
    │ controler   │ character varying           │                 │ not null  │            │ extended │                       │             │
    │ download_ts │ timestamp without time zone │                 │ not null  │ now()      │ plain    │                       │             │
    │ error_count │ integer                     │                 │           │            │ plain    │                       │             │
    │ http_status │ integer                     │                 │           │            │ plain    │                       │             │
    │ comment     │ character varying           │                 │           │            │ extended │                       │             │
    └─────────────┴─────────────────────────────┴─────────────────┴───────────┴────────────┴──────────┴───────────────────────┴─────────────┘
    Index :
        "ix_gn2pg_import_download_log_error_count" btree (error_count)
        "ix_gn2pg_import_download_log_http_status" btree (http_status)
        "ix_gn2pg_import_download_log_source" btree (source)
    Méthode d'accès : heap

                                                    Table « gn2pg_import.increment_log »
    ┌───────────┬─────────────────────────────┬─────────────────┬───────────┬────────────┬──────────┬───────────────────────┬─────────────┐
    │  Colonne  │            Type             │ Collationnement │ NULL-able │ Par défaut │ Stockage │ Cible de statistiques │ Description │
    ├───────────┼─────────────────────────────┼─────────────────┼───────────┼────────────┼──────────┼───────────────────────┼─────────────┤
    │ source    │ character varying           │                 │ not null  │            │ extended │                       │             │
    │ controler │ character varying           │                 │ not null  │            │ extended │                       │             │
    │ last_ts   │ timestamp without time zone │                 │ not null  │ now()      │ plain    │                       │             │
    └───────────┴─────────────────────────────┴─────────────────┴───────────┴────────────┴──────────┴───────────────────────┴─────────────┘
    Index :
        "increment_log_pkey" PRIMARY KEY, btree (source)
    Méthode d'accès : heap

                        Index « gn2pg_import.increment_log_pkey »
    ┌─────────┬───────────────────┬───────┬────────────┬──────────┬───────────────────────┐
    │ Colonne │       Type        │ Clé ? │ Définition │ Stockage │ Cible de statistiques │
    ├─────────┼───────────────────┼───────┼────────────┼──────────┼───────────────────────┤
    │ source  │ character varying │ oui   │ source     │ extended │                       │
    └─────────┴───────────────────┴───────┴────────────┴──────────┴───────────────────────┘
    clé primaire, btree, pour la table « gn2pg_import.increment_log »

            Index « gn2pg_import.ix_gn2pg_import_data_json_id_data »
    ┌─────────┬─────────┬───────┬────────────┬──────────┬───────────────────────┐
    │ Colonne │  Type   │ Clé ? │ Définition │ Stockage │ Cible de statistiques │
    ├─────────┼─────────┼───────┼────────────┼──────────┼───────────────────────┤
    │ id_data │ integer │ oui   │ id_data    │ plain    │                       │
    └─────────┴─────────┴───────┴────────────┴──────────┴───────────────────────┘
    btree, pour la table « gn2pg_import.data_json »

            Index « gn2pg_import.ix_gn2pg_import_data_json_uuid »
    ┌─────────┬──────┬───────┬────────────┬──────────┬───────────────────────┐
    │ Colonne │ Type │ Clé ? │ Définition │ Stockage │ Cible de statistiques │
    ├─────────┼──────┼───────┼────────────┼──────────┼───────────────────────┤
    │ uuid    │ uuid │ oui   │ uuid       │ plain    │                       │
    └─────────┴──────┴───────┴────────────┴──────────┴───────────────────────┘
    btree, pour la table « gn2pg_import.data_json »

            Index « gn2pg_import.ix_gn2pg_import_download_log_error_count »
    ┌─────────────┬─────────┬───────┬─────────────┬──────────┬───────────────────────┐
    │   Colonne   │  Type   │ Clé ? │ Définition  │ Stockage │ Cible de statistiques │
    ├─────────────┼─────────┼───────┼─────────────┼──────────┼───────────────────────┤
    │ error_count │ integer │ oui   │ error_count │ plain    │                       │
    └─────────────┴─────────┴───────┴─────────────┴──────────┴───────────────────────┘
    btree, pour la table « gn2pg_import.download_log »

            Index « gn2pg_import.ix_gn2pg_import_download_log_http_status »
    ┌─────────────┬─────────┬───────┬─────────────┬──────────┬───────────────────────┐
    │   Colonne   │  Type   │ Clé ? │ Définition  │ Stockage │ Cible de statistiques │
    ├─────────────┼─────────┼───────┼─────────────┼──────────┼───────────────────────┤
    │ http_status │ integer │ oui   │ http_status │ plain    │                       │
    └─────────────┴─────────┴───────┴─────────────┴──────────┴───────────────────────┘
    btree, pour la table « gn2pg_import.download_log »

                Index « gn2pg_import.ix_gn2pg_import_download_log_source »
    ┌─────────┬───────────────────┬───────┬────────────┬──────────┬───────────────────────┐
    │ Colonne │       Type        │ Clé ? │ Définition │ Stockage │ Cible de statistiques │
    ├─────────┼───────────────────┼───────┼────────────┼──────────┼───────────────────────┤
    │ source  │ character varying │ oui   │ source     │ extended │                       │
    └─────────┴───────────────────┴───────┴────────────┴──────────┴───────────────────────┘
    btree, pour la table « gn2pg_import.download_log »

                            Index « gn2pg_import.meta_json_pk »
    ┌─────────┬───────────────────┬───────┬────────────┬──────────┬───────────────────────┐
    │ Colonne │       Type        │ Clé ? │ Définition │ Stockage │ Cible de statistiques │
    ├─────────┼───────────────────┼───────┼────────────┼──────────┼───────────────────────┤
    │ uuid    │ uuid              │ oui   │ uuid       │ plain    │                       │
    │ source  │ character varying │ oui   │ source     │ extended │                       │
    └─────────┴───────────────────┴───────┴────────────┴──────────┴───────────────────────┘
    clé primaire, btree, pour la table « gn2pg_import.datasets_json »

                            Index « gn2pg_import.pk_source_data »
    ┌─────────┬───────────────────┬───────┬────────────┬──────────┬───────────────────────┐
    │ Colonne │       Type        │ Clé ? │ Définition │ Stockage │ Cible de statistiques │
    ├─────────┼───────────────────┼───────┼────────────┼──────────┼───────────────────────┤
    │ id_data │ integer           │ oui   │ id_data    │ plain    │                       │
    │ source  │ character varying │ oui   │ source     │ extended │                       │
    │ type    │ character varying │ oui   │ type       │ extended │                       │
    └─────────┴───────────────────┴───────┴────────────┴──────────┴───────────────────────┘
    clé primaire, btree, pour la table « gn2pg_import.data_json »



Full download
+++++++++++++

To full download json datas into synthese_json table, run : 

.. code-block:: bash

    gn2pg_cli --full <myconfigfile>

    

Incremental download
++++++++++++++++++++

To update datas into synthese_json table, run : 

.. code-block:: bash

    gn2pg_cli --update <myconfigfile>


To automate the launching of updates, you can write the cron task using the following command, for example every 30 minutes.

.. code-block::

    */30 * * * * /usr/bin/env bash -c "source <path to python environment>/bin/activate && gn2pg_cli --update <myconfigfile>" > /dev/null 2>&1


Logs
++++

Log files are stored in ``$HOME/.gn2pg/log`` directory.


Import datas into GeoNature datas
+++++++++++++++++++++++++++++++++

Default script to auto populate GeoNature is called "synthese". 

.. code-block:: bash

    gn2pg_cli --custom-script to_gnsynthese <myconfigfile>


.. tip::

    You can also replacing synthese script by your own scripts, using file path instead of ``to_gnsynthese``.
