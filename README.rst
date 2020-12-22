**************
 Gn2Gn Client
**************

.. image:: https://img.shields.io/badge/python-3.x-yellowgreen
   :target: https://www.python.org/
.. image:: https://img.shields.io/badge/code%20style-black-black
   :target: https://github.com/psf/black
.. image:: https://img.shields.io/badge/licence-AGPL--3.0-blue
   :target: https://opensource.org/licenses/AGPL-3.0

This project provides an import tool between GeoNature_ instances (client side).
Widely inspired from `ClientApiVN <https://framagit.org/lpo/Client_API_VN/>`_


.. contents:: Topics

.. warning::
    Actually not usable, in active development.



.. image:: ./Gn2Gn.png
    :align: center
    :alt: Logo DREAL AuRA


Project Setup
=============

Gn2Gn Client can be installed by running ``pip``. It requires Python 3.7.4+ to run.

.. code-block:: bash

    python3 -m pip install https://github.com/lpoaura/gn2gn_client/archive/dev.zip


Issues
======

Please report any bugs or requests that you have using the `GitHub issue tracker <https://github.com/lpoaura/gn2gn_client/issues>`_!

HowTo
=====

Help
####

.. code-block:: bash

    gn2gn_cli --help

Init config file
################

.. code-block:: bash

    gn2gn_cli --init


This command init a TOML config file in user home dir, named as you want

Config file is structured as this. ``source`` block can be duplicate as many as needed (on block for each source).

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



InitDB  Schema and tables
#########################

.. code-block:: bash

    gn2gn_cli --json-tables-create myconfigfile


Import datas from geonature 
###########################

Coming soon...

Contributing
############

All devs must be done in forks. 

Pull requests must be pulled to `dev` branch. For example with this command:

.. code-block:: bash

    gh repo fork --clone lpoaura/gn2gn_client


Install project and development requirements (require `poetry <https://python-poetry.org/>`_):

.. code-block:: bash

    poetry install

Make your devs and pull requests.


Licence
=======

`GNU AGPLv3 <https://www.gnu.org/licenses/gpl.html>`_

Team
====

* `@lpofredc <https://github.com/lpofredc/>`_ (`LPO Auvergne-Rhône-Alpes <https://github.com/lpoaura/>`_), main developper


.. image:: https://raw.githubusercontent.com/lpoaura/biodivsport-widget/master/images/LPO_AuRA_l250px.png
    :align: center
    :height: 100px
    :alt: Logo LPOAuRA

.. _GeoNature: https://geonature.fr/

------------

With the financial support of the `DREAL Auvergne-Rhône-Alpes <http://www.auvergne-rhone-alpes.developpement-durable.gouv.fr/>`_.

.. image:: https://data.lpo-aura.org/web/images/blocmarque_pref_region_auvergne_rhone_alpes_rvb_web.png
    :align: center
    :height: 100px
    :alt: Logo DREAL AuRA