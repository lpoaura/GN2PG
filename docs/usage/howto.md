(how-to)=

# HowTo

## Help

```bash
gn2pg_cli --help
```

## Manage configurations

You can easily manage your configuration files using `gn2pg_cli config`:

```text
usage: gn2pg_cli config [-h] (--init [INIT] | --list | --read [READ] | --edit [EDIT])

options:
  -h, --help     show this help message and exit
  --init [INIT]  Initialize the TOML configuration file
  --list         Lister les configurations
  --read [READ]  Select and view config file
  --edit [EDIT]  Select and view config file
```

This following command will init a TOML config file within `~/.gn2pg` hidden directory (in user `$HOME` directory), named as you want. **PLEASE DO NOT SPECIFY PATH!**

```bash
gn2pg_cli config --init <myconfigfile>
```

Config file is structured as this. `[[source]]` block can be duplicate as many as needed (one block for each source).

```TOML
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
# Duplicate this block for each source (1 source = 1 export)
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
# Additional export API QueryStrings to filter or order data, you can add multiple "orderby" columns by separating column names with ":"
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
```

:::{tip}
You can add variable in source block `enable = false` to disable a source
:::

:::{tip}
Default `data_type` (if not defined) is `synthese_with_cd_nomenclature`, this type is used to conditioning triggers to populate `gn_synthese.synthese`. This value can be customized for each source with key `data_type`.
Provided `data_type` are `synthese_with_label` for standard GeoNature export, `synthese_with_cd_nomenclature` for a standard export using `cd_nomenclature`, `synthese_with_metadata` for and advanced export included metadata
:::

:::{tip}
It is highly recommanded to set and `orderby` setting in `[source.query_strings]` block (coming soon, actually in development in export module) to order correctly data in export
:::

:::{tip}
You can specify globally page length to download and store data from API (default is 1000) by configuring `max_page_length` value in optional `[tuning]` block.
:::

## InitDB Schema and tables

Commands are under `gn2pg_cli db` subcommands:

```text
usage: gn2pg_cli db [-h] (--custom-script [CUSTOM_SCRIPT] | --json-tables-create) [file]

positional arguments:
  file                  Configuration file name

options:
  -h, --help            show this help message and exit
  --custom-script [CUSTOM_SCRIPT]
                        Exécute un script SQL personnalisé dans la base de données, la valeur par défaut est "to_gnsynthese". Vous pouvez également utiliser votre propre
                        script en utilisant le chemin de fichier absolu à la place de "to_gnsynthese"
  --json-tables-create  Créer ou recréer des tables json
```

To create json tables where datas will be downloaded, run :

```bash
gn2pg_cli db --json-tables-create <myconfigfile>
```

```{image} ../_static/gn2pg_import_models.png
:align: center
:width: 100%
:alt: Database models
```

If you want to apply default database scripts to populate a GeoNature database, you can execute:

```bash 
gn2pg_cli db --custom_script to_gnsynthese <myconfigfile>
```

:::{note}
You can also replacing synthese script by your own scripts, using file path instead of `to_gnsynthese`.
:::


:::{attention}
When data from GN2PG is inserted into the `geonature.synthese` table using the supplied trigger, existing triggers on geonature.synthese are executed a posteriori and can override data values from the GN2PG source (for example, the id_nomenclature_sensitivity value).
:::


## Data download

Data download can be executed using `gn2pg_cli download` commands.

```text
usage: gn2pg_cli download [-h] (--full | --update) [file]

positional arguments:
  file        Configuration file name

options:
  -h, --help  show this help message and exit
  --full      Effectuer un téléchargement complet
  --update    Effectuer un téléchargement incrémentiel
```

### Full download

To full download json datas into `data_json` table, run :

```bash
gn2pg_cli download --full <myconfigfile>
```

### Incremental download

To update datas into `data_json` table, run :

```bash
gn2pg_cli download --update <myconfigfile>
```

To automate the launching of updates, you can write the cron task using the following command, for example every 30 minutes.

```
*/30 * * * * /usr/bin/env bash -c "source <path to python environment>/bin/activate && gn2pg_cli download --update <myconfigfile>" > /dev/null 2>&1
```

## Logs

Log files are stored in `$HOME/.gn2pg/log` directory.