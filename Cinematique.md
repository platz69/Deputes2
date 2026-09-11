Cinématique du point de vue des fichiers temporaires :

                               > défini dans le Code        > TENDANCES_COULEUR_FILE

ORGANES_FOLDER                 >  calcul_groupes()          > GROUPES_ABREV_LIBELLE_FILE

ACTEURS_FOLDER                 >  charger_dossier_acteur()  > acteurs_info{}

SCRUTINS_FOLDER                >  calcul_acteurs_et_votes() > ACTEUR_VOTE_FILE,
                                                              ACTEURS_FILE

ACTEUR_VOTE_FILE,
ACTEURS_FILE,
GROUPES_ABREV_LIBELLE_FILE,
TENDANCES_COULEUR_FILE         >  calcul_tendance_vote()    > TENDANCE_VOTE_FILE

ACTEUR_VOTE_FILE               >  calcul_distances_acteur() > DISTANCES_ACTEUR_ACTEUR_FILE

ACTEUR_VOTE_FILE,
TENDANCE_VOTE_FILE             >  calcul_distances_acteurs_tendance() > DISTANCES_ACTEUR_TENDANCE_FILE

ACTEURS_FILE                   >  charger_fichier_acteur()   > {}

TENDANCE_VOTE_FILE             > calcul_distances_tendances() > DISTANCES_TENDANCE_TENDANCE_FILE

ACTEURS_FILE,
GROUPES_ABREV_LIBELLE_FILE,
TENDANCES_COULEUR_FILE,
DISTANCES_ACTEUR_TENDANCE_FILE >  acteur_tendance_relle()    > ACTEUR_TENDANCE_RELLE

ACTEUR_VOTE_FILE               >  calcul_participation()     > ACTEURS_PARTICIP_FILE

ACTEURS_FILE,
GROUPES_ABREV_LIBELLE_FILE,
ACTEURS_PARTICIP_FILE          >  calcul_labels()            > ACTEUR_LABEL_FILE

ACTEURS_FILE,
GROUPES_ABREV_LIBELLE_FILE,
ACTEURS_PARTICIP_FILE          >  statistiques()             >  None

DISTANCES_ACTEUR_ACTEUR_FILE   >  reduire()                  > ACTEURS_X_Y_FILE,
                                                               ACTEURS_X_Y_Z_FILE

DISTANCES_TENDANCE_TENDANCE_FILE >  reduire_tendances()      > TENDANCES_X_Y_FILE,
                                                               TENDANCES_X_Y_Z_FILE 

ACTEURS_X_Y_FILE,
ACTEURS_X_Y_Z_FILE,
ACTEURS_FILE,
GROUPES_ABREV_LIBELLE_FILE,
TENDANCES_COULEUR_FILE,
ACTEUR_LABEL_FILE               > affiche_graphe_*()         > None  