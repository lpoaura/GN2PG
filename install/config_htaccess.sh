#!/bin/bash

echo "Check if htpasswd existe déjà ..."
if [ -f /etc/apache2/.htpasswd ]; then
echo "Voici votre fichier avec votre liste d'utilisateur et leur mdp chiffré : $(cat /etc/apache2/.htpasswd)"
echo "-----"
read -p "Appuyer sur une touche pour quitter. Appuyer sur 'Y' ou 'y' pour continuer et ajouter une nouvel utilisateur au fichier htpasswd  " choice

if [ "$choice" = 'y' ] || [ "$choice" = 'Y' ]; then
    echo "Choisi un nom d'utilisateur"
    read varname
    sudo htpasswd /etc/apache2/.htpasswd $varname
    exit
fi
else
    echo "Fichier  /etc/apache2/.htpasswd non existant, choisi un nom d'utilisateur"
    read varname
    sudo htpasswd -c /etc/apache2/.htpasswd $varname
    exit
fi


