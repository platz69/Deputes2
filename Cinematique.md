Cinématique du point de vue des fichiers temporaires :

ORGANES_FOLDER                                      ---  calcul_groupes()            ---> ORGANES_FILE
ACTEURS_FOLDER                                      ---  charger_dossier_acteur()    ---> acteurs_info{}
SCRUTINS_FOLDER                                     ---  calcul_acteurs_et_votes()   ---> TABLE_VOTES_FILE, ACTEURS_FILE

TABLE_VOTES_FILE                                    ---  calcul_distances()          ---> TABLE_DISTANCES_FILE
ACTEURS_FILE                                        ---  charger_fichier_acteur()    ---> {}
TABLE_VOTES_FILE                                    ---  calcul_participation()      ---> ACTEURS_PARTICIP_FILE
TABLE_VOTES_FILE, TABLE_DISTANCES_FILE, ACTEURS_FILE, ORGANES_FILE
                                                    ---statistiques()--->  None
ACTEURS_FILE, ORGANES_FILE, ACTEURS_PARTICIP_FILE   ---  acteur_label()              ---> str
ACTEURS_FILE, ORGANES_FILE, ACTEURS_PARTICIP_FILE   ---  calcul_labels()             ---> ACTEUR_LABEL_FILE
TABLE_DISTANCES_FILE                                ---  reduire()                   ---> COORDONNES_FILE
ACTEURS_FILE, GROUPES_FILE, ACTEURS_PARTICIP_FILE, COORDONNES_3D_FILE
                                                    ---> calcul_barycentres()        ---> BARYCENTRES_FILE
ORGANES_FILE, ACTEURS_FILE, COORDONNES_FILE, ACTEURS_PARTICIP_FILE
                                                    ---> affiche_graphe()            ---> None  