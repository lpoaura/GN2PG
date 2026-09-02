# Process

## ENG

The data are downloaded from a standardized GeoNature export from the export module as follows:

- Verification of the connection and authentication to the source GeoNature instance.
- Retrieving the URL of the export module (according to the API `/api/gn_commons/modules`)
- Initial full download (option `--full`):
  - Downloading of the first batch of data (number limited by the `limit` parameter of the export, `1000` by default)
  - Calculation of the number of pages of the export.
  - Downloading and uploading in database page by page.
- Upload (option `--update`):
  - Retrieving updates (INSERT, UPDATE, DELETE) from source.
  - Deleting DELETE data from the database.
  - Downloading and UPSERT data.

### Transfer statuses

The current transfer stage is stored in the `xfer_status` field of the import log.

| Status | Description |
| --- | --- |
| `init` | The transfer has been created but processing has not started yet. |
| `importing data` | Data or metadata is currently being downloaded and stored. |
| `delete` | Records deleted from the source are currently being removed locally. |
| `success` | All requested transfer steps completed successfully. |
| `failed` | The transfer stopped because an API or processing error occurred. |

## FR

Les données sont téléchargées depuis un export standardisé GeoNature à partir du module d'export comme suit:

- Vérification de la connexion et l'authentification à l'instance GeoNature source
- Récupération de l'URL du module d'export (d'après l'API `/api/gn_commons/modules`)
- Téléchargement complet initial (option `download --full`):
  - Téléchargement du premier lot de données (nombre limité par le paramètre `limit` de l'export, `1000` par défaut)
  - Calcul du nombre de pages de l'export.
  - Téléchargement et chargement en base de données pages par pages.
- Chargement `update`:
  - Récupération des données d'API des mises à jour (`INSERT`, `UPDATE`, `DELETE`).
  - Suppression des données `DELETE` de la base de données.
  - Téléchargement et `UPSERT` des données (`INSERT ... ON CONFLICT ... DO UPDATE`).

### Statuts des transferts

L'étape courante du transfert est enregistrée dans le champ `xfer_status` du journal
d'import.

| Statut | Description |
| --- | --- |
| `init` | Le transfert a été créé, mais son traitement n'a pas encore commencé. |
| `importing data` | Les données ou métadonnées sont en cours de téléchargement et d'enregistrement. |
| `delete` | Les enregistrements supprimés à la source sont en cours de suppression locale. |
| `success` | Toutes les étapes demandées du transfert se sont terminées avec succès. |
| `failed` | Le transfert s'est arrêté à la suite d'une erreur d'API ou de traitement. |
