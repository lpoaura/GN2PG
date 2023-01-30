**************
 GN2PG Client
**************

.. image:: https://img.shields.io/badge/python-3.7+-yellowgreen
   :target: https://www.python.org/
.. image:: https://img.shields.io/badge/PostgreSQL-10+-blue
   :target: https://www.postgresql.org/
.. image:: https://img.shields.io/badge/packaging%20tool-poetry-important
   :target: https://python-poetry.org/
.. image:: https://img.shields.io/badge/code%20style-black-black
   :target: https://github.com/psf/black
.. image:: https://img.shields.io/badge/licence-AGPL--3.0-blue
   :target: https://opensource.org/licenses/AGPL-3.0
.. image:: https://app.fossa.com/api/projects/git%2Bgithub.com%2Flpoaura%2FGN2PG.svg?type=shield
   :target: https://app.fossa.com/projects/git%2Bgithub.com%2Flpoaura%2FGN2PG?ref=badge_shield

This project provides an import data from GeoNature_ instances to a PostgreSQL database (client side).
Widely inspired from `ClientApiVN <https://framagit.org/lpo/Client_API_VN/>`_


.. contents:: Topics

.. image:: ./docs/source/_static/src_gn2pg.png
    :align: center
    :alt: Project logo


Project Setup
=============

GN2PG Client can be installed by running ``pip``. It requires Python 3.7.4 or above to run.

.. code-block:: bash

    pip install gn2pg-client


Issues
======

Please report any bugs or requests that you have using the `GitHub issue tracker <https://github.com/lpoaura/gn2pg_client/issues>`_!

HowTo
=====

Help
####

.. code-block:: bash

    gn2pg_cli --help

Init config file
################

This command init a TOML config file within ``~/.gn2pg`` hidden directory (in user ``HOME`` directory), named as you want. PLEASE DO NOT SPECIFY PATH!

.. code-block:: bash

    gn2pg_cli --init <myconfigfile>


Config file is structured as this. ``[[source]]`` block can be duplicate as many as needed (one block for each source).

The ``data_type`` value on each source is used to characterize the type of data. This value is used to identify which triggers to be triggered when inserting, updating or deleting data.
Current provided trigger configs are:

* ``synthese_with_cd_nomenclature`` which provide triggers to insert basically data on synthese and generate basic metadatas (acquisition framework and datasets). Source query sample is provided in file `geonature_export_sinp_with_cd_nomenclature.sql <https://github.com/lpoaura/GN2PG/tree/main/data/source_samples/geonature_export_sinp_with_cd_nomenclature.sql>`_
* ``synthese_with_metadata`` which provide triggers to insert data in synthese and populate most of the metadata data (acquisition frameworks, datasets, actors such as organisms and roles, territories, etc.). Source query sample is provided in file `geonature_export_sinp_with_metadata.sql <https://github.com/lpoaura/GN2PG/tree/main/data/source_samples/geonature_export_sinp_with_metadata.sql>`_

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
    # Data type is facultative. By default the value is 'synthese'. Therefore, triggers from to_gnsynthese.sql are not activated.
    # If you want to insert your data into a GeoNature database please choose either 'synthese_with_cd_nomenclature' or 'synthese_with_metadata'.
    # If not, delete the line.
    data_type = "synthese_with_cd_nomenclature"


    [[source]]
    # Source configuration
    name = "Source2"
    user_name = "<monuser>"
    user_password = "<monPwd>"
    url = "<http://geonature2/>"
    export_id = 1
    data_type = "synthese_with_cd_nomenclature"



.. tip::

   You can add variable in source block ``enable = false`` to disable a source


InitDB  Schema and tables
#########################

To create json tables where datas will be stored, run :

.. code-block:: bash

    gn2pg_cli --json-tables-create <myconfigfile>


Full download
#############

To download all datas from API, run :

.. code-block:: bash

    gn2pg_cli --full <myconfigfile>

Incremental download
####################

To update data since last download, run :

.. code-block:: bash

    gn2pg_cli --update <myconfigfile>


To automate the launching of updates, you can write the cron task using the following command, for example every 30 minutes.

.. code-block:: cron

    */30 * * * * /usr/bin/env bash -c "source <path to python environment>/bin/activate && gn2pg_cli --update <myconfigfile>" > /dev/null 2>&1


Debug mode
############

Debug mode can be activated using ``--verbose`` CLI argument

Logs
####

Log files are stored in ``$HOME/.gn2pg/log`` directory.

Import datas into GeoNature datas
#################################

Default script to auto populate GeoNature is called "to_gnsynthese".

.. code-block:: bash

    gn2pg_cli --custom-script to_gnsynthese <myconfigfile>


.. tip::

    You can also replacing synthese script by your own scripts, using file path instead of ``to_gnsynthese``.


Contributing
============

All devs must be done in forks (see `GitHub doc <https://docs.github.com/en/get-started/quickstart/fork-a-repo>`_).

Pull requests must be pulled to `dev` branch.

Install project and development requirements (require `poetry <https://python-poetry.org/>`_):

.. code-block:: bash

    poetry install

Make your devs and pull requests.

Test `gn2pg_cli` in dev mode by running this command:

.. code-block:: bash

    poetry run gn2pg_cli <options>

Renew requirements file for non poetry developers
#################################################

.. code-block:: bash

    poetry export -f requirements.txt > requirements.txt


Licence
=======

`GNU AGPLv3 <https://www.gnu.org/licenses/gpl.html>`_

Team
====

* `@lpofredc <https://github.com/lpofredc/>`_ (`LPO Auvergne-Rhône-Alpes <https://github.com/lpoaura/>`_), main developer

.. image:: https://raw.githubusercontent.com/lpoaura/biodivsport-widget/master/images/LPO_AuRA_l250px.png
    :align: center
    :height: 100px
    :alt: Logo LPOAuRA

* @ophdlv (Natural Solution), contributor
* @mvergez (Natural Solution), contributor
* @andriacap (Natural Solution), contributor
* @Adrien-Pajot (Natural Solution), contributor

.. _GeoNature: https://geonature.fr

------------

With the financial support of the `DREAL Auvergne-Rhône-Alpes <http://www.auvergne-rhone-alpes.developpement-durable.gouv.fr/>`_ and the `Office français de la biodiversité <https://www.ofb.gouv.fr/>`_.

.. image:: https://data.lpo-aura.org/web/images/blocmarque_pref_region_auvergne_rhone_alpes_rvb_web.png
    :align: center
    :height: 100px
    :alt: Logo DREAL AuRA

.. image:: https://www.ofb.gouv.fr/sites/default/files/logo-ofb.png
    :align: center
    :height: 100px
    :alt: Logo OFB
