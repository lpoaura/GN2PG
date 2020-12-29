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

 
InitDB  Schema and tables
+++++++++++++++++++++++++

To create json tables where datas will be downloaded, run : 

.. code-block:: bash

    gn2gn_cli --json-tables-create <myconfigfile>


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

.. warning::

    [WIP] Not yet implemented!