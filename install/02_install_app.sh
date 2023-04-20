#!/bin/bash

set -o pipefail

if [ ! -f settings.ini ]; then
  cp settings.ini.sample settings.ini
  echo "Remplissez le fichier de settings.ini dans le dossier : $PWD  "
  exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
. "${SCRIPT_DIR}/utils"

#get app path
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
DIR_CONFIG="${DIR}/assets"


cd $BASE_DIR
#Installation des dépendances liées au dashboard
poetry config virtualenvs.create true --local
poetry config virtualenvs.in-project true --local
poetry install --extras=dashboard


# Configuration systemd
write_log "Configuration systemd"

export GN2PG_DIR=$(readlink -e "${0%/*}")
export GUNICORN_WORKERS_TO_SET=$GUNICORN_WORKERS
export GUNICORN_PORT_TO_SET=$GUNICORN_PORT
export GUNICORN_TIMEOUT_TO_SET=$GUNICORN_TIMEOUT
export APPLICATION_ROOT_TO_SET=$APPLICATION_ROOT
export SERVER_NAME_TO_SET=$SERVER_NAME

cd $DIR_CONFIG

envsubst '${USER}' < tmpfiles-gn2pg.conf | sudo tee /etc/tmpfiles.d/gn2pg.conf || exit 1
sudo systemd-tmpfiles --create /etc/tmpfiles.d/gn2pg.conf || exit 1
envsubst '${USER} ${GN2PG_DIR} ${GUNICORN_WORKERS_TO_SET} ${GUNICORN_PORT_TO_SET} ${GUNICORN_TIMEOUT_TO_SET}' < gn2pg.service | sudo tee /etc/systemd/system/gn2pg.service || exit 1
sudo systemctl daemon-reload || exit 1

# Configuration logrotate
envsubst '${USER}' < log_rotate | sudo tee /etc/logrotate.d/gn2pg

# Configuration apache
envsubst '${APPLICATION_ROOT_TO_SET} ${GUNICORN_PORT_TO_SET}' < gn2pg_apache.conf | sudo tee /etc/apache2/conf-available/gn2pg.conf || exit 1

echo -e "\nSouhaitez vous créer un nouveau virtualhost avec un domaine que vous avez choisi ou vous avez déjà un nom de domaine existant ? "
read -p "Appuyer sur 'N' ou 'n' pour ne pas ajouter de virtualHost. Appuyer sur 'Y' ou 'y' pour continuer et ajouter un nouveau virtualhost avec le SERVER_NAME : '$SERVER_NAME' , choisi en config " choice

if [ "$choice" = 'y' ] || [ "$choice" = 'Y' ]; then
    echo "Creation du fichier /etc/apache2/site-available/gn2pg.conf "
    envsubst '${SERVER_NAME_TO_SET}' < gn2pg_virtualhost.conf | sudo tee /etc/apache2/sites-available/gn2pg.conf || exit 1
fi

sudo a2enmod proxy || exit 1
sudo a2enmod proxy_http || exit 1
# you may need to restart apache2 if proxy & proxy_http was not already enabled


echo "Vous pouvez maintenant : "
echo "- démarrer gn2pg avec la commande : sudo systemctl start gn2pg"
echo "- activer les conf avec la commande : sudo a2enconf gn2pg"
echo "- activer les conf virtualhost avec la commande : sudo a2ensite gn2pg (si vous avez choisi d'ajouter cette config)"
