**INTRODUCTION**

Ce script utilise les données publiques du site **data.assemblee-nationale.fr** afin de réaliser des statistiques sur les députés et votes en séance publique de l'Assemblée nationale.

Je m'intéresse plus particulièrement aux similitudes de comportement entre les votants afin de déterminer des groupes réels, indépendamment de l'étiquette politique revendiquée.

Pour cela chaque député est représenté par un vecteur à +/- 4000 dimensions (nombre de scrutins dans une législature)
puis un algorithme de type UMPA réduit cet espace à 2 dimensions afin de faire apparaître des groupes sur un graphique.

La régle de distance entre chaque député est calculée en fonction de leurs votes :
- même vote : distance = +0
- 1 abstention/absence et un vote pour/contre : distance = +1
- 2 votes opposés : distance = +2

**MODE D'EMPLOI**

     "o": calcule les organes
     "v": calcule les votes
     "d": calcule les distances
     "u": réduction de dimension par UMPA
     "m": réduction de dimension par MDS

**EXEMPLE DE RÉSULTAT**
