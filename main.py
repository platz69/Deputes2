from unittest import case

import pandas as pd
import numpy as np
import umap

VOTES_FILE       = "votes.csv"
DISTANCES_FILE   = "distances.csv"
COORDINATES_FILE = "coordinates.csv"


def calcul_distances():
    # Lecture du fichier CSV
    # La première colonne (s1...s10) est utilisée comme index
    df = pd.read_csv(VOTES_FILE, sep=';', index_col=0)

    # Les colonnes représentent les points
    points = df.columns

    # Conversion en tableau NumPy
    X = df.to_numpy()

    # Nombre de points
    n = X.shape[1]

    # Matrice des distances
    dist = np.zeros((n, n), dtype=int)

    # Calcul des distances de Manhattan
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
    distance_df.to_csv(DISTANCES_FILE)


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


def mds(csv_file, n_components=2, random_state=42, plot=True):
    """
    Reduce a square distance matrix using Metric MDS.

    Parameters
    ----------
    csv_file : str
        Path to CSV containing a square distance matrix.
    n_components : int
        Number of output dimensions (2 or 3).
    random_state : int
        Random seed for reproducibility.
    plot : bool
        If True, display a scatter plot.

    Returns
    -------
    embedding : pandas.DataFrame
        Coordinates of each item.
    """

    # Read distance matrix
    D = pd.read_csv(csv_file, index_col=0)

    # Metric MDS
    mds = MDS(
        n_components=n_components,
        dissimilarity="precomputed",
        random_state=random_state,
        normalized_stress="auto"
    )

    coords = mds.fit_transform(D.values)

    embedding = pd.DataFrame(
        coords,
        index=D.index,
        columns=[f"MDS{i+1}" for i in range(n_components)]
    )

    if plot and n_components == 2:
        plt.figure(figsize=(6, 6))
        plt.scatter(embedding["MDS1"], embedding["MDS2"])

        for name, (x, y) in embedding.iterrows():
            plt.text(x, y, name, fontsize=10)

        plt.xlabel("MDS1")
        plt.ylabel("MDS2")
        plt.title("Metric MDS")
        plt.axis("equal")
        plt.tight_layout()
        plt.show()

    return embedding


choix = input("d: distances, u: réduction UMA, m: MDS ")
match choix:
    case "d": calcul_distances()
    case "u": umap_2d(DISTANCES_FILE, COORDINATES_FILE)
    case "m": mds(DISTANCES_FILE)

