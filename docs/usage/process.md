# Process

## ENG

The data are downloaded from a standardized GeoNature export from the export module as follows:

- Verification of the connection and authentication to the source GeoNature instance.
- Retrieving the URL of the export module (according to the API `/api/gn_commons/modules`)
- Initial full download (option `--full`):
  : - Downloading of the first batch of data (number limited by the `limit` parameter of the export, `1000` by default)
    - Calculation of the number of pages of the export: `max_offset = int(presp["total_filtered"] / presp["limit"]) - 1`.
    - Downloading and uploading in database page by page.
- Upload (option `--update`):
  : - Retrieving updates (INSERT, UPDATE, DELETE) from source.
    - Deleting DELETE data from the database.
    - Downloading and UPSERT data.

## FR

Les données sont téléchargées depuis un export standardisé GeoNature à partir du module d'export comme suit:

- Vérification de la connexion et l'authentification à l'instance GeoNature source
- Récupération de l'URL du module d'export (d'après l'API `/api/gn_commons/modules`)
- Téléchargement complet initial (option `--full`):
  : - Téléchargement du premier lot de données (nombre limité par le paramètre `limit` de l'export, `1000` par défaut)
    - Calcul du nombre de pages de l'export: `max_offset = int(presp["total_filtered"] / presp["limit"]) - 1`
    - Téléchargement et chargement en base de données pages par pages.
- Chargement `update`:
  : - Récupération des données d'API des mises à jour (INSERT, UPDATE, DELETE).
    - Suppression des données DELETE de la base de données
    - Téléchargement et UPSERT des données INSERT ou UPDATE
