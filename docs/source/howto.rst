HowTo
=====

Help
++++

.. code-block:: bash

    gn2gn_cli --help

Init config file
++++++++++++++++

This command init a TOML config file within ``~/.gn2gn`` hidden directory (in user ``HOME`` directory), named as you want. PLEASE DO NOT SPECIFY PATH!

.. code-block:: bash

    gn2gn_cli --init <myconfigfile>


Config file is structured as this. ``[[source]]`` block can be duplicate as many as needed (one block for each source).

.. code-block:: TOML

    # Gn2Gn configuration file

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

   By default, data type is ``synthese``, and this type is used conditioning triggers to populate ``gn_synthese.synthese``. This value can be customized for each source with key ``data_type``.

.. tip::

   You can specify globally page length to download and store data from API (default is 1000) by configuring ``max_page_length`` value in optional ``[tuning]`` block.

 
InitDB Schema and tables
+++++++++++++++++++++++++

To create json tables where datas will be downloaded, run : 

.. code-block:: bash

    gn2gn_cli --json-tables-create <myconfigfile>

.. code-block::

                                                       Table « gn2gn_import.data_json »
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
        "ix_gn2gn_import_data_json_id_data" btree (id_data)
        "ix_gn2gn_import_data_json_uuid" btree (uuid)
    Méthode d'accès : heap

                                            Table « gn2gn_import.datasets_json »
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

                                                    Table « gn2gn_import.download_log »
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
        "ix_gn2gn_import_download_log_error_count" btree (error_count)
        "ix_gn2gn_import_download_log_http_status" btree (http_status)
        "ix_gn2gn_import_download_log_source" btree (source)
    Méthode d'accès : heap

                                                    Table « gn2gn_import.increment_log »
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

                        Index « gn2gn_import.increment_log_pkey »
    ┌─────────┬───────────────────┬───────┬────────────┬──────────┬───────────────────────┐
    │ Colonne │       Type        │ Clé ? │ Définition │ Stockage │ Cible de statistiques │
    ├─────────┼───────────────────┼───────┼────────────┼──────────┼───────────────────────┤
    │ source  │ character varying │ oui   │ source     │ extended │                       │
    └─────────┴───────────────────┴───────┴────────────┴──────────┴───────────────────────┘
    clé primaire, btree, pour la table « gn2gn_import.increment_log »

            Index « gn2gn_import.ix_gn2gn_import_data_json_id_data »
    ┌─────────┬─────────┬───────┬────────────┬──────────┬───────────────────────┐
    │ Colonne │  Type   │ Clé ? │ Définition │ Stockage │ Cible de statistiques │
    ├─────────┼─────────┼───────┼────────────┼──────────┼───────────────────────┤
    │ id_data │ integer │ oui   │ id_data    │ plain    │                       │
    └─────────┴─────────┴───────┴────────────┴──────────┴───────────────────────┘
    btree, pour la table « gn2gn_import.data_json »

            Index « gn2gn_import.ix_gn2gn_import_data_json_uuid »
    ┌─────────┬──────┬───────┬────────────┬──────────┬───────────────────────┐
    │ Colonne │ Type │ Clé ? │ Définition │ Stockage │ Cible de statistiques │
    ├─────────┼──────┼───────┼────────────┼──────────┼───────────────────────┤
    │ uuid    │ uuid │ oui   │ uuid       │ plain    │                       │
    └─────────┴──────┴───────┴────────────┴──────────┴───────────────────────┘
    btree, pour la table « gn2gn_import.data_json »

            Index « gn2gn_import.ix_gn2gn_import_download_log_error_count »
    ┌─────────────┬─────────┬───────┬─────────────┬──────────┬───────────────────────┐
    │   Colonne   │  Type   │ Clé ? │ Définition  │ Stockage │ Cible de statistiques │
    ├─────────────┼─────────┼───────┼─────────────┼──────────┼───────────────────────┤
    │ error_count │ integer │ oui   │ error_count │ plain    │                       │
    └─────────────┴─────────┴───────┴─────────────┴──────────┴───────────────────────┘
    btree, pour la table « gn2gn_import.download_log »

            Index « gn2gn_import.ix_gn2gn_import_download_log_http_status »
    ┌─────────────┬─────────┬───────┬─────────────┬──────────┬───────────────────────┐
    │   Colonne   │  Type   │ Clé ? │ Définition  │ Stockage │ Cible de statistiques │
    ├─────────────┼─────────┼───────┼─────────────┼──────────┼───────────────────────┤
    │ http_status │ integer │ oui   │ http_status │ plain    │                       │
    └─────────────┴─────────┴───────┴─────────────┴──────────┴───────────────────────┘
    btree, pour la table « gn2gn_import.download_log »

                Index « gn2gn_import.ix_gn2gn_import_download_log_source »
    ┌─────────┬───────────────────┬───────┬────────────┬──────────┬───────────────────────┐
    │ Colonne │       Type        │ Clé ? │ Définition │ Stockage │ Cible de statistiques │
    ├─────────┼───────────────────┼───────┼────────────┼──────────┼───────────────────────┤
    │ source  │ character varying │ oui   │ source     │ extended │                       │
    └─────────┴───────────────────┴───────┴────────────┴──────────┴───────────────────────┘
    btree, pour la table « gn2gn_import.download_log »

                            Index « gn2gn_import.meta_json_pk »
    ┌─────────┬───────────────────┬───────┬────────────┬──────────┬───────────────────────┐
    │ Colonne │       Type        │ Clé ? │ Définition │ Stockage │ Cible de statistiques │
    ├─────────┼───────────────────┼───────┼────────────┼──────────┼───────────────────────┤
    │ uuid    │ uuid              │ oui   │ uuid       │ plain    │                       │
    │ source  │ character varying │ oui   │ source     │ extended │                       │
    └─────────┴───────────────────┴───────┴────────────┴──────────┴───────────────────────┘
    clé primaire, btree, pour la table « gn2gn_import.datasets_json »

                            Index « gn2gn_import.pk_source_data »
    ┌─────────┬───────────────────┬───────┬────────────┬──────────┬───────────────────────┐
    │ Colonne │       Type        │ Clé ? │ Définition │ Stockage │ Cible de statistiques │
    ├─────────┼───────────────────┼───────┼────────────┼──────────┼───────────────────────┤
    │ id_data │ integer           │ oui   │ id_data    │ plain    │                       │
    │ source  │ character varying │ oui   │ source     │ extended │                       │
    │ type    │ character varying │ oui   │ type       │ extended │                       │
    └─────────┴───────────────────┴───────┴────────────┴──────────┴───────────────────────┘
    clé primaire, btree, pour la table « gn2gn_import.data_json »



Full download
+++++++++++++

To full download json datas into synthese_json table, run : 

.. code-block:: bash

    gn2gn_cli --full <myconfigfile>

Incremental download
++++++++++++++++++++

.. warning::

    [WIP] Not yet implemented!


Logs
++++

Log files are stored in ``$HOME/.gn2gn/log`` directory.


Import datas into GeoNature datas
+++++++++++++++++++++++++++++++++

Default script to auto populate GeoNature is called "synthese". 

.. code-block:: bash

    gn2gn_cli --custom-script synthese <myconfigfile>


.. tip::

    You can also replacing synthese script by your own scripts, using file path instead of ``synthese``.