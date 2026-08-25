Cinématique des fichiers temporaires :

ORGANES_FOLDER                                      ---  calcul_organes()               ---> ORGANES_FILE
ACTEURS_FOLDER                                     ---  charger_noms_prenoms_acteurs() ---> acteurs_info
SCRUTINS_FOLDER                                     ---  calcul_votes()                 ---> VOTES_FILE + ACTEURS_FILE
VOTES_FILE                                          ---  calcul_distances()             ---> DISTANCES_FILE
VOTES_FILE + DISTANCES_FILE + ACTEURS_FILE + ORGANES_FILE + DISTANCES_FILE  ---statistiques()---> ACTEURS_PARTICIP_FILE
ACTEURS_FILE + ORGANES_FILE + ACTEURS_PARTICIP_FILE ---  label_acteur()                 ---> str
ACTEURS_FILE + ORGANES_FILE + ACTEURS_PARTICIP_FILE ---  calcul_labels()()              ---> ACTEUR_LABEL_FILE
DISTANCES_FILE                                      ---  reduire()                      ---> COORDONNES_FILE
GROUPES_COULEURS_FILE + ORGANES_FILE + ACTEURS_FILE + COORDONNES_FILE + ACTEURS_PARTICIP_FILE  ---affiche_graphe() ---> None                           ---affiche_graphe_2d() --->



