# bibliothèques standard
import os
import json

# bibliothèques externes
import pandas as pd

# entrées
SCRUTINS_FOLDER       = "Scrutins"
ORGANES_FOLDER        = "Organes"
GROUPES_COULEURS_FILE = "groupes_couleurs.csv"

# sorties
ACTEURS_GROUP_FILE = "acteurs_groupes.csv"
VOTES_FILE       = "votes.csv"
DISTANCES_FILE   = "distances.csv"
COORDINATES_FILE = "coordinates.csv"
ORGANES_FILE     = "organes.csv"


def calcul_organes():

    # ouverture du fichier organes en écriture
    with open(ORGANES_FILE, "w", encoding="utf-8", newline='') as organe_file:

    # Parcourir les fichiers JSON du dossier Organes
     for file in sorted(os.listdir(ORGANES_FOLDER)):
            if file.endswith(".json"):
                json_path = os.path.join(ORGANES_FOLDER, file)
                with open(json_path, encoding='utf-8') as f:
                    data           = json.load(f)
                    organe         = data['organe']['uid']
                    type_organe    = data['organe']['codeType']
                    libelle_abrev  = str(data['organe']['libelleAbrev']).upper()
                    libelle        = data['organe']['libelle']
                    organe_file.write(";".join([organe, type_organe, libelle_abrev, libelle]) + "\n")


def calcul_votes():

    # Dictionnaire pour stocker les votes : {acteurRef: {scrutin_uid: vote_value}}
    votes_dict = {}
    scrutins_list = []
    votant_dict = {}

    # Parcourir les fichiers JSON du dossier Scrutins
    for file in sorted(os.listdir(SCRUTINS_FOLDER)):
        if file.endswith(".json"):
            scrutin_id = file.replace(".json", "")
            scrutins_list.append(scrutin_id)

            json_path = os.path.join(SCRUTINS_FOLDER, file)
            with open(json_path, encoding='utf-8') as f:
                data    = json.load(f)
                groups  = data['scrutin']['ventilationVotes']['organe']['groupes']['groupe']

                # if not isinstance(groups, list):
                #     groups = [groups]

                # Pour chaque groupe, extraire les votes
                for group in groups:

                    # Traiter les différentes catégories de vote
                    vote_value_map = {
                        'pours': 1,
                        'contres': -1,
                        'abstentions': 0,
                        'nonVotants': 0
                    }

                    # parcours des 4 catégories 'pours', 'contres', 'abstentions', 'nonVotants'
                    vote_par_categorie = group['vote']['decompteNominatif']

                    for category, vote_value in vote_value_map.items():
                        if vote_par_categorie[category]:
                            votants = vote_par_categorie[category]['votant']
                            if not isinstance(votants, list):
                                votants = [votants]

                            # parcours des votants d'une catégorie
                            for votant in votants:
                                acteur_ref = votant['acteurRef']
                                if acteur_ref not in votes_dict:
                                    votes_dict[acteur_ref] = {}
                                votes_dict[acteur_ref][scrutin_id] = vote_value

                                # profitons-en pour stocker le groupe parlementaire du votant
                                votant_dict[acteur_ref] = group['organeRef']

    # Créer le CSV avec en-têtes des scrutins et votes
    with open(VOTES_FILE, "w", encoding="utf-8", newline='') as f:
        # En-tête avec les UIDs des scrutins
        header = [''] + scrutins_list
        f.write(";".join(header) + "\n")

        # Pour chaque votant, écrire son ID et ses votes
        for acteur_ref in sorted(votes_dict.keys()):
            row = [acteur_ref]
            for scrutin_uid in scrutins_list:
                vote_value = votes_dict[acteur_ref].get(scrutin_uid, '')
                row.append(str(vote_value) if vote_value != '' else '0')
            f.write(";".join(row) + "\n")

    # Créer le CSV des ovtants_groupe parlementaire
    with open(ACTEURS_GROUP_FILE, "w", encoding="utf-8", newline='') as f:
        for acteur_ref in sorted(votes_dict.keys()):
            f.write(";".join([acteur_ref, votant_dict[acteur_ref]]) + "\n")

    print(f"Fichier {VOTES_FILE} créé avec succès !")


def calcul_distances():
    import numpy as np

    # Lecture du fichier CSV, la première colonne est utilisée comme index
    df = pd.read_csv(VOTES_FILE, sep=';', index_col=0) # noqa

    deputes = df.index

    # Conversion en tableau NumPy
    votes = df.to_numpy()

    # Nombre de points
    nb_deputes = df.shape[0]
    nb_votes   = df.shape[1]

    # Matrice des distances
    dist = np.zeros((nb_deputes, nb_deputes), dtype=int)

    # Calcul des distances (même vote : +0, une abstention : +1, opposé : +2)
    for i in range(nb_deputes):
        for j in range(i, nb_deputes):
            d = np.sum(np.abs(votes[i,:] - votes[j,:]))
            dist[i, j] = d
            dist[j, i] = d

    # Conversion en DataFrame pour conserver les noms
    distance_df = pd.DataFrame(dist, index=deputes, columns=deputes)

    # Affichage
    print(distance_df)

    # Sauvegarde éventuelle
    distance_df.to_csv(DISTANCES_FILE, sep=';')


def umap_2d(input_csv=DISTANCES_FILE,
            output_csv=COORDINATES_FILE,
            n_neighbors=3, # increase to 15 (?) for 3000
            min_dist=0,
            random_state=42):

    import umap

    # Read the data
    distances = pd.read_csv(input_csv, index_col=0) # noqa

    reducer = umap.UMAP(
        n_components=2,
        metric="precomputed",
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        random_state=random_state
    )

    reduc = reducer.fit_transform(distances)

    result = pd.DataFrame(
        reduc,
        index=distances.index,
        columns=["x", "y"]
    )

    # Sauvegarde du fichier des coordonnées
    result.to_csv(COORDINATES_FILE, sep=';')


def mds_2d(distance_file,
           n_components=2,
           random_state=42,
           plot=True):
    """
    Réduit une matrice de distances avec MDS
    """

    from sklearn.manifold import MDS
    import matplotlib.pyplot as plt
    import mplcursors

    # Matrice des distances
    distances = pd.read_csv(distance_file, sep=';', header=0, index_col=0) # noqa

    # MDS
    mds = MDS(
        n_components=n_components,
        dissimilarity="precomputed",
        random_state=random_state,
        normalized_stress="auto"
    )

    coords = mds.fit_transform(distances.values)

    embedding = pd.DataFrame(
        coords,
        index=distances.index,
        columns=[f"MDS{i+1}" for i in range(n_components)]
    )

    # Sauvegarde du fichier des coordonnées
    embedding.to_csv(COORDINATES_FILE, sep=';')

    # acteur > groupe> couleur
    acteurs_groupes        = pd.read_csv(ACTEURS_GROUP_FILE, sep=";", header=None).set_index(0)[1].to_dict() # noqa
    organes                = pd.read_csv(ORGANES_FILE, sep=";", header=None).set_index(0)[2].to_dict() # noqa
    groupes_abrev_couleurs = pd.read_csv(GROUPES_COULEURS_FILE, sep=";", header=None).set_index(0)[2].to_dict() # noqa

    if plot and n_components == 2:
        plt.figure(figsize=(8, 8))

        fig, ax = plt.subplots()

        xs = []
        ys = []
        colors = []
        labels = []

        for acteur_ref, (x, y) in embedding.iterrows():
            acteur_couleur = groupes_abrev_couleurs[organes[acteurs_groupes[acteur_ref]]]
            xs.append(x)
            ys.append(y)
            colors.append(acteur_couleur)
            labels.append(acteur_ref)

        sc = ax.scatter(xs, ys, s=80, color=colors)

        cursor = mplcursors.cursor(sc, hover=True)

        @cursor.connect("add")
        def on_add(sel):
            sel.annotation.set_text(labels[sel.index])

        # for acteur_ref, (x, y) in embedding.iterrows():
        #     acteur_couleur = groupes_abrev_couleurs[organes[acteurs_groupes[acteur_ref]]]
        #
        #     plt.scatter(
        #         x,
        #         y,
        #         s=80,
        #         color=acteur_couleur
        #     )
        #
        #     plt.text(
        #         x,
        #         y,
        #         acteur_ref,
        #         fontsize=10,
        #         ha="left",
        #         va="bottom",
        #         color=acteur_couleur
        #     )

        plt.title("Projection MDS des votants")
        plt.axis("equal")
        plt.tight_layout()
        plt.show()

    input('Continuer')
    return embedding


choix = input("o: organes, v: votes, d: distances, u: réduction UMA, m: réduction MDS ")
match choix:
    case "o": calcul_organes()
    case "v": calcul_votes()
    case "d": calcul_distances()
    case "u": umap_2d(DISTANCES_FILE, COORDINATES_FILE)
    case "m": mds_2d(DISTANCES_FILE)

