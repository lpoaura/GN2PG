Process
=======

Les données sont téléchargées depuis un export standardisé GeoNature via le module d'export comme suit:


* Vérification de la connexion et l'authentification à l'instance GeoNature source
* Récupération de l'URL du module d'export (d'après l'API `/api/gn_commons/modules`
* Chargment `full`:
    * Téléchargement du premier lot de données (nombre limité par le paramètre `limit` de l'export, `1000` par défaut)
    * Calcul du nombre de pages de l'export: `max_offset = int(presp["total_filtered"] / presp["limit"]) - 1`
    * Téléchargement et chargement en base de données pages par pages.
* Chargement `update`:
    * Récupération des données d'API des mises à jour (INSERT, UPDATE, DELETE).
    * Suppression des données DELETE de la base de données
    * Téléchargement et UPSERT des données INSERT ou UPDATE 

