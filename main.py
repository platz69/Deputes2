import numpy as np
import umap

VOTES_FILE       = "votes.csv"
DISTANCES_FILE   = "distances.csv"
COORDINATES_FILE = "coordinates.csv"


def calcul_distances():
    # Lecture du fichier CSV, la première colonne (s1...s10) est utilisée comme index
    df = pd.read_csv(VOTES_FILE, sep=';', index_col=0)

    # Les colonnes représentent les points
    points = df.columns

    # Conversion en tableau NumPy
    X = df.to_numpy()

    # Nombre de points
    n = X.shape[1]

    # Matrice des distances
    dist = np.zeros((n, n), dtype=int)

    # Calcul des distances (même vote : +0, une abstention : +1, opposé : +2)
    for i in range(n):
        for j in range(i, n):
            d = np.sum(np.abs(X[:, i] - X[:, j]))
            dist[i, j] = d
            dist[j, i] = d

    # Conversion en DataFrame pour conserver les noms
    distance_df = pd.DataFrame(dist, index=points, columns=points)

    # Affichage
    print(distance_df)

    # Sauvegarde éventuelle
    distance_df.to_csv(DISTANCES_FILE, sep=';')


def umap_2d(input_csv=DISTANCES_FILE,
            output_csv=COORDINATES_FILE,
            n_neighbors=3, # increase to 15 (?) for 3000
            min_dist=0,
            random_state=42):

    # Read the data
    df = pd.read_csv(input_csv, index_col=0)

    # UMAP expects one sample per row.
    # Since the points are the columns, transpose the matrix.
    X = df.T

    reducer = umap.UMAP(
        n_components=2,
        metric="precomputed",
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        random_state=random_state
    )

    Y = reducer.fit_transform(X)

    result = pd.DataFrame(
        Y,
        index=X.index,
        columns=["x", "y"]
    )

    result.to_csv(output_csv, sep=';')


import pandas as pd
from sklearn.manifold import MDS
import matplotlib.pyplot as plt


def mds(distance_file,
                    voters_file="votants.csv",
                    n_components=2,
                    random_state=42,
                    plot=True):
    """
    Réduit une matrice de distances avec MDS et remplace les identifiants
    v1, v2... par les noms contenus dans votants.csv.
    """

    # Matrice des distances
    D = pd.read_csv(distance_file, index_col=0)

    # Lecture des votants (séparateur ;)
    voters = pd.read_csv(
        voters_file,
        sep=";",
        header=None,
        names=["id", "nom", "prenom"]
    )

    # Dictionnaire : v1 -> Laurent FABIUS
    labels = {
        row.id: f"{row.prenom} {row.nom}"
        for _, row in voters.iterrows()
    }

    # MDS
    mds = MDS(
        n_components=n_components,
        dissimilarity="precomputed",
        random_state=random_state,
        normalized_stress="auto"
    )

    coords = mds.fit_transform(D.values)

    embedding = pd.DataFrame(
        coords,
        index=D.index.map(lambda x: labels.get(x, x)),
        columns=[f"MDS{i+1}" for i in range(n_components)]
    )

    if plot and n_components == 2:
        plt.figure(figsize=(8, 8))

        plt.scatter(
            embedding["MDS1"],
            embedding["MDS2"],
            s=80,
            color="steelblue"
        )

        for name, (x, y) in embedding.iterrows():
            plt.text(
                x,
                y,
                name,
                fontsize=10,
                ha="left",
                va="bottom"
            )

        plt.xlabel("MDS1")
        plt.ylabel("MDS2")
        plt.title("Projection MDS des votants")
        plt.axis("equal")
        plt.tight_layout()
        plt.show()

    return embedding


choix = input("d: distances, u: réduction UMA, m: MDS ")
match choix:
    case "d": calcul_distances()
    case "u": umap_2d(DISTANCES_FILE, COORDINATES_FILE)
    case "m": mds(DISTANCES_FILE)

