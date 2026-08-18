**INTRODUCTION**

Ce script utilise les données publiques du site **data.assemblee-nationale.fr** afin de réaliser des statistiques sur les députés et votes en séance publique de l'Assemblée nationale.

Je cherche à identifier les similitudes de comportement entre les votants (qui ne tienne donc pas compte des groupes parlementaires).

Pour cela chaque député est représenté par un vecteur à +/- 4000 dimensions (nombre de scrutins dans une législature)
puis un algorithme UMAP ou MDS réduit cet espace à 3 dimensions afin de faire apparaître des nuages de points sur un graphique.

La régle de distance entre chaque député est calculée en fonction de leurs votes :
- même vote : distance = +0
- 1 abstention/absence et un vote pour/contre : distance = +1
- 2 votes opposés : distance = +2

**MODE D'EMPLOI**

Les options ci-dessous sont à exécuter dans l'ordre, chacune produisant un ou plusieurs fichiers .csv nécessaires à l'étape suivante.

     "o": parcourt le répertoire "organes" pour produire un fichier organes.csv
     "v": parcourt le répertoire "scrutins" pour produire un fichier votes.csv
     "d": utilise le fichier "votes.csv" pour produire un fichier distances.csv
     "u": réduction de dimension par UMPA
     "m": réduction de dimension par MDS et affichage du graphique

**FICHIERS UTILISÉS**

https://data.assemblee-nationale.fr/acteurs/historique-des-deputes :
AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip (13Mo)
/json/acteur : 1 fichier PAxxxx.json pour chacun des  3117 députés existants/ayant existé
/json/organe : 1 fichier POxxxx.json pour chacun des 10813 organes existants/ayant existé, en particulier 43 groupes parlementaires identifiés par la balise json "codeType": "GP"

https://data.assemblee-nationale.fr/archives-16e/votes :
Scrutins.json.zip
/json : 1 fichier VTANR5L16Vxxxx.json pour chacun des 4106 scrutins de la XVIème législature (2017-2022)

**EXEMPLE DE RÉSULTAT**

![projection_3d.html](..\projection_3d.html)