# bibliothèques standard
import math
import os
import json
from typing import Dict

# entrées
ACTEURS_FOLDER        = "acteur"               # dossier où l'on dépose les fichiers PAxxxx.json
ORGANES_FOLDER        = "organe"               # dossier où l'on dépose les fichiers POxxxx.json
SCRUTINS_FOLDER       = "scrutin"              # dossier où l'on dépose les fichiers VTANR5LxxVxxxx.json
GROUPES_COULEURS_FILE = "groupes_couleurs.csv" # id_groupe;libellé;tendance;couleur

# sorties
TEMP_FOLDER         = "temp"                   # dossier temporaire pour les fichiers CSV intermédiaires
os.makedirs(TEMP_FOLDER, exist_ok=True)

ACTEURS_PARTICIP_FILE = os.path.join(TEMP_FOLDER, "acteurs_particip.csv") # id_acteur;nombre_de_votes
ACTEURS_FILE          = os.path.join(TEMP_FOLDER, "acteurs.csv")          # id_acteur;id_groupe;nom;prenom
VOTES_FILE            = os.path.join(TEMP_FOLDER, "votes.csv")            # id_acteur;vote1;vote2;...;vote4000;...
DISTANCES_FILE        = os.path.join(TEMP_FOLDER, "distances.csv")        # id_acteur;distance_acteur1;distance_acteur2;distance_acteur3;...
COORDONNES_FILE       = os.path.join(TEMP_FOLDER, "coordonnes.csv")       # id_acteur;x;y
COORDONNES_3D_FILE    = os.path.join(TEMP_FOLDER, "coordonnes_3d.csv")    # id_acteur;x;y;z
ORGANES_FILE          = os.path.join(TEMP_FOLDER, "organes.csv")          # id_organe;type_organe;libelle_abrev;libelle


def calcul_organes() -> None:
    """Produit le fichier organes.csv à partir des fichiers JSON du dossier organes"""

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


def charger_noms_prenoms_acteurs() -> Dict[str, Dict[str, str]]:
    """Charge les noms et prénoms des acteurs depuis les fichiers JSON du dossier acteurs"""

    acteurs_info = {}
    
    for file in sorted(os.listdir(ACTEURS_FOLDER)):
        if file.endswith(".json"):
            json_path = os.path.join(ACTEURS_FOLDER, file)
            try:
                with open(json_path, encoding='utf-8') as f:
                    data = json.load(f)
                    acteur_uid = data['acteur']['uid']['#text']
                    etat_civil = data['acteur']['etatCivil']['ident']
                    nom = etat_civil.get('nom', '')
                    prenom = etat_civil.get('prenom', '')
                    acteurs_info[acteur_uid] = {'nom': nom, 'prenom': prenom}
            except (KeyError, json.JSONDecodeError):
                pass
    
    return acteurs_info


def calcul_votes() -> None:
    """Produit le fichier votes.csv et acteurs_groupes.csv à partir des fichiers JSON du dossier scrutins"""

    # Dictionnaires
    votes_dict    = {}
    scrutins_list = []
    votant_dict   = {}

    # Charge les noms et prénoms des acteurs
    acteurs_info = charger_noms_prenoms_acteurs()

    # Parcourir les fichiers JSON du dossier scrutins
    for file in sorted(os.listdir(SCRUTINS_FOLDER)):
        if file.endswith(".json") and file.startswith("VTA"): # attention il y a un fichier VTCxxx à éviter, on ne prend que les VTAxxx !
            scrutin_id = file.replace(".json", "")
            scrutins_list.append(scrutin_id)

            json_path = os.path.join(SCRUTINS_FOLDER, file)
            with open(json_path, encoding='utf-8') as f:
                data    = json.load(f)
                groups  = data['scrutin']['ventilationVotes']['organe']['groupes']['groupe']

                # Pour chaque groupe, extraire les votes
                for group in groups:

                    # parcours des 4 catégories 'pours', 'contres', 'abstentions', 'nonVotants'
                    vote_value_map = {
                        'pours': 1,
                        'contres': -1,
                        'abstentions': 0,
                        'nonVotants': 0
                    }

                    vote_par_categorie = group['vote']['decompteNominatif']

                    for category, vote_value in vote_value_map.items():
                        if vote_par_categorie[category]:
                            votants = vote_par_categorie[category]['votant']
                            if not isinstance(votants, list):
                                votants = [votants]

                            # parcours des votants d'une catégorie
                            for votant in votants:
                                acteur_id = votant['acteurRef']
                                if acteur_id not in votes_dict:
                                    votes_dict[acteur_id] = {}
                                votes_dict[acteur_id][scrutin_id] = vote_value

                                # profitons-en pour stocker le groupe parlementaire du votant
                                votant_dict[acteur_id] = group['organeRef']

    # Créer le CSV avec en-têtes des scrutins et votes
    with open(VOTES_FILE, "w", encoding="utf-8", newline='') as f:
        # En-tête avec les UIDs des scrutins
        header = [''] + scrutins_list
        f.write(";".join(header) + "\n")

        # Pour chaque votant, écrire une ligne avec son ID et ses votes
        for acteur_id in sorted(votes_dict.keys()):
            row = [acteur_id]
            for scrutin_uid in scrutins_list:
                vote_value = votes_dict[acteur_id].get(scrutin_uid, '')
                row.append(str(vote_value) if vote_value != '' else '0')
            f.write(";".join(row) + "\n")

    # Créer le CSV des votants_groupe parlementaire avec noms et prénoms
    with open(ACTEURS_FILE, "w", encoding="utf-8", newline='') as f:
        for acteur_id in sorted(votes_dict.keys()):
            info = acteurs_info.get(acteur_id, {'nom': '', 'prenom': ''})
            f.write(";".join([acteur_id, votant_dict[acteur_id], info['nom'], info['prenom']]) + "\n")


def calcul_distances() -> None:
    """ Produit le fichier distances.csv à partir du fichier votes.csv """
    import numpy as np
    import pandas as pd

    # Lecture du fichier CSV, la première colonne est utilisée comme index
    df = pd.read_csv(VOTES_FILE, sep=';', index_col=0) # noqa

    deputes = df.index
    votes = df.to_numpy()
    nb_deputes = df.shape[0]

    # Initialisation de la matrice des distances avec des zéros
    dist = np.zeros((nb_deputes, nb_deputes), dtype=int)

    # Calcul des distances (même vote : +0, une abstention : +1, opposé : +2)
    for i in range(nb_deputes):
        # la matrice est symétrique, on ne parcourt que la moitié supérieure
        for j in range(i, nb_deputes):
            d = np.sum(np.abs(votes[i,:] - votes[j,:]))
            dist[i, j] = d
            dist[j, i] = d

    # Sauvegarde du tableau des distances
    distance_df = pd.DataFrame(dist, index=deputes, columns=deputes)
    distance_df.to_csv(DISTANCES_FILE, sep=';')


def statistiques() -> None:
    """Produit le fichier acteurs_particip.csv à partir du fichier votes.csv

    Affiche dans la console les 5 acteurs ayant le plus participé et les 5 les plus absents
    (affichage en bleu). Affiche aussi les 5 paires d'acteurs les plus proches et les 5 les plus éloignées
    """
    import pandas as pd
    import os

    df = pd.read_csv(VOTES_FILE, sep=';', index_col=0)

    # Convertir en numérique et remplacer les non-nombres par 0
    df_num = df.apply(pd.to_numeric, errors='coerce').astype(int).fillna(0)

    # Participation = somme des valeurs non-nulles de la ligne
    participation = (df_num != 0).sum(axis=1)

    # Écriture du fichier ACTEURS_PARTICIP_FILE
    with open(ACTEURS_PARTICIP_FILE, 'w', encoding='utf-8', newline='') as f:
        f.write("acteur_id;nombre_de_votes\n")
        for acteur, count in participation.items():
            f.write(f"{acteur};{count}\n")

    # Dictionnaire acteur_id: nom + prénom
    acteurs_info = charger_noms_prenoms_acteurs()

    # Dictionnaire acteur_id : groupe_id
    acteurs_groupes = pd.read_csv(ACTEURS_FILE, sep=';', header=None).set_index(0)[1].to_dict()

    # Dictionnaire organe_id : libellé abrégé
    organes_map = pd.read_csv(ORGANES_FILE, sep=';', header=None).set_index(0)[2].to_dict()

    def label_for(acteur_id: str) -> str:
        info   = acteurs_info.get(acteur_id)
        prenom = info.get('prenom').strip()
        nom    = info.get('nom').strip()
        name   = (prenom + ' ' + nom).strip()

        grp_id    = acteurs_groupes.get(acteur_id)
        grp_label = organes_map.get(grp_id)

        return f"{name} ({grp_label})"

    # Pour l'affichage en bleu
    blue = '\033[34m'
    reset = '\033[0m'

    top5    = participation.sort_values(ascending=False).head(5)
    bottom5 = participation.sort_values(ascending=True).head(5)

    print(blue + "Top 5 des participants:" + reset)
    for i, (acteur, count) in enumerate(top5.items(), start=1):
        print(f"{i}. {label_for(str(acteur))}: {count}")

    print(blue + "Top 5 des absents:" + reset)
    for i, (acteur, count) in enumerate(bottom5.items(), start=1):
        print(f"{i}. {label_for(str(acteur))}: {count}")

    # Maintenant calculer les paires les plus proches/éloignées à partir de DISTANCES_FILE
    if not os.path.exists(DISTANCES_FILE):
        print(f"Fichier des distances {DISTANCES_FILE} introuvable. Impossible de calculer les paires.")
        return

    try:
        distances_df = pd.read_csv(DISTANCES_FILE, sep=';', index_col=0)
    except Exception as e:
        print(f"Erreur en lisant {DISTANCES_FILE} : {e}")
        return

    pairs = []
    actors = list(distances_df.index)
    n = len(actors)
    for i in range(n):
        for j in range(i+1, n): # on ne prend que la moitié supérieure de cette matrice symétrique
            d = distances_df.iat[i, j]
            pairs.append((actors[i], actors[j], float(d)))

    if not pairs:
        print("Aucune paire trouvée dans le fichier des distances.")
        return

    pairs_sorted = sorted(pairs, key=lambda t: t[2])
    closest5     = pairs_sorted[:5]
    farthest5    = pairs_sorted[-5:][::-1]

    print(blue + "\n5 paires les plus proches (distance la plus petite):" + reset)
    for i, (a, b, d) in enumerate(closest5, start=1):
        print(f"{i}. {label_for(a)}  -  {label_for(b)} : {d}")

    print(blue + "\n5 paires les plus éloignées (distance la plus grande):" + reset)
    for i, (a, b, d) in enumerate(farthest5, start=1):
        print(f"{i}. {label_for(a)}  -  {label_for(b)} : {d}")

# def umap_2d(n_neighbors: int = 3, min_dist: float = 0, random_state: int = 42) -> None:
#     """ Produit le fichier coordonnes.csv à partir du fichier distances.csv en utilisant l'algorithme UMAP"""
#     import pandas as pd
#     import umap
#
#     # Chargement du tableau des distances
#     distances = pd.read_csv(DISTANCES_FILE, sep=';', index_col=0)
#
#     # réduction en 2D avec UMAP
#     reducer = umap.UMAP(
#         n_components=2,
#         metric="precomputed",
#         n_neighbors=n_neighbors,
#         min_dist=min_dist,
#         random_state=random_state
#     )
#
#     reduc = reducer.fit_transform(distances)
#
#     result = pd.DataFrame(
#         reduc,
#         index=distances.index,
#         columns=["x", "y"]
#     )
#
#     # Arrondir les coordonnées à 2 décimales
#     result = result.round(2)
#
#     # Sauvegarde du fichier des coordonnées (2 décimales)
#     result.to_csv(COORDONNES_FILE, sep=';', float_format='%.2f')
#
#
# def umap_3d(n_neighbors: int = 15, min_dist: float = 0.1, random_state: int = 42) -> None:
#     """Produit le fichier coordonnes_3d.csv à partir du fichier distances.csv en utilisant l'algorithme UMAP"""
#     import pandas as pd
#     import umap
#
#     # Chargement du tableau des distances
#     distances = pd.read_csv(DISTANCES_FILE, sep=';', index_col=0)
#
#     # réduction en 3D avec UMAP
#     reducer = umap.UMAP(
#         n_components=3,
#         metric="precomputed",
#         n_neighbors=n_neighbors,
#         min_dist=min_dist,
#         random_state=random_state
#     )
#
#     reduc = reducer.fit_transform(distances)
#
#     result = pd.DataFrame(
#         reduc,
#         index=distances.index,
#         columns=["x", "y", "z"]
#     )
#
#     # Arrondir les coordonnées à 2 décimales
#     result = result.round(2)
#
#     # Sauvegarde du fichier des coordonnées 3D (2 décimales)
#     result.to_csv(COORDONNES_3D_FILE, sep=';', float_format='%.2f')
#
#
# def mds_2d(n_components: int = 2, dissimilarity: str = "precomputed", random_state: int = 42) -> None:
#     """Produit le fichier coordonnes.csv à partir du fichier distances.csv en utilisant l'algorithme MDS"""
#     import pandas as pd
#     from sklearn.manifold import MDS
#
#     # Chargement du tableau des distances
#     distances = pd.read_csv(DISTANCES_FILE, sep=';', header=0, index_col=0)
#
#     # réduction en 2D avec MDS
#     mds = MDS(
#         n_components=n_components,
#         dissimilarity=dissimilarity,
#         random_state=random_state
#     )
#
#     coords = mds.fit_transform(distances.values)
#
#     # Sauvegarde du fichier des coordonnées
#     embedding = pd.DataFrame(
#         coords,
#         index=distances.index,
#         columns=[f"MDS{i+1}" for i in range(n_components)]
#     )
#
#     # Arrondir les coordonnées à 2 décimales et sauvegarde
#     embedding = embedding.round(2)
#     embedding.to_csv(COORDONNES_FILE, sep=';', float_format='%.2f')
#
#     return
#
#
# def mds_3d(n_components: int = 3, dissimilarity: str = "precomputed", random_state: int = 42) -> None:
#     """Produit le fichier coordonnes_3d.csv à partir du fichier distances.csv en utilisant l'algorithme MDS"""
#     import pandas as pd
#     from sklearn.manifold import MDS
#
#     # Chargement du tableau des distances
#     distances = pd.read_csv(DISTANCES_FILE, sep=';', header=0, index_col=0)
#
#     # réduction en 3D avec MDS
#     mds = MDS(
#         n_components=n_components,
#         dissimilarity=dissimilarity,
#         random_state=random_state
#     )
#
#     coords = mds.fit_transform(distances.values)
#
#     # Sauvegarde du fichier des coordonnées 3D
#     embedding = pd.DataFrame(
#         coords,
#         index=distances.index,
#         columns=["x", "y", "z"]
#     )
#
#     # Arrondir les coordonnées à 2 décimales et sauvegarde
#     embedding = embedding.round(2)
#     embedding.to_csv(COORDONNES_3D_FILE, sep=';', float_format='%.2f')
#
#     return


def reduire(algo: str, n_components: int, **kwargs) -> None:
    """Produit coordonnes.csv (2D) ou coordonnes_3d.csv (3D) via UMAP ou MDS"""
    import pandas as pd

    distances = pd.read_csv(DISTANCES_FILE, sep=';', index_col=0)

    if algo == "umap":
        import umap
        reducer = umap.UMAP(n_components=n_components, metric="precomputed", **kwargs)
    elif algo == "mds":
        from sklearn.manifold import MDS
        reducer = MDS(n_components=n_components, dissimilarity="precomputed", **kwargs)
    else:
        raise ValueError(f"algo inconnu: {algo}")

    coords = reducer.fit_transform(distances if algo == "mds" else distances)
    columns = ["x", "y"] if n_components == 2 else ["x", "y", "z"]
    result = pd.DataFrame(coords, index=distances.index, columns=columns).round(2)

    out_file = COORDONNES_FILE if n_components == 2 else COORDONNES_3D_FILE
    result.to_csv(out_file, sep=';', float_format='%.2f')


def affiche_graphe_2d() -> None:
    """Affiche un graphe 2D à partir du fichier coordonnes.csv et des fichiers auxiliaires"""
    import pandas as pd
    import matplotlib.pyplot as plt
    import mplcursors

    # lecture du fichier des coordonnées
    embedding = pd.read_csv(COORDONNES_FILE, sep=';', index_col=0)

    # Chargement des tables auxiliaires
    acteurs_groupes  = pd.read_csv(ACTEURS_FILE,    sep=';', header=None).set_index(0)[1].to_dict()
    acteurs_nom      = pd.read_csv(ACTEURS_FILE,    sep=';', header=None).set_index(0)[2].to_dict()
    acteurs_prenom   = pd.read_csv(ACTEURS_FILE,    sep=';', header=None).set_index(0)[3].to_dict()
    organes          = pd.read_csv(ORGANES_FILE,          sep=';', header=None).set_index(0)[2].to_dict()
    groupes_couleurs = pd.read_csv(GROUPES_COULEURS_FILE, sep=';', header=None).set_index(0)[3].to_dict()

    # Lecture du nombre de votes par acteur pour dimensionner les points
    participation = pd.read_csv(ACTEURS_PARTICIP_FILE, sep=';', index_col=0)
    vote_counts   = participation['nombre_de_votes'].to_dict()

    votes     = list(vote_counts.values())
    min_votes = min(votes) if votes else 0
    max_votes = max(votes) if votes else 1

    def point_size(act_id: str) -> float:
        nb_votes = vote_counts.get(act_id, min_votes)
        if max_votes == min_votes:
            return 80
        return 20 + 200 * (nb_votes - min_votes) / (max_votes - min_votes)

    # construction du graphe
    fig, ax = plt.subplots(figsize=(8, 8))

    xs = []
    ys = []
    colors = []
    sizes = []
    labels = []

    for acteur_id, (x, y) in embedding.iterrows():
        try:
            groupe_label = organes[acteurs_groupes[acteur_id]]
            acteur_couleur = groupes_couleurs[groupe_label]
            xs.append(x)
            ys.append(y)
            colors.append(acteur_couleur)
            sizes.append(point_size(str(acteur_id)))
            labels.append(acteurs_prenom[acteur_id] + " " + acteurs_nom[acteur_id] + ", " + groupe_label)
        except (KeyError, TypeError, ValueError):
            # si un acteur manque dans les tables, on l'ignore
            continue

    sc = ax.scatter(xs, ys, s=sizes, color=colors)

    # ajout des étiquettes au survol à la souris
    cursor = mplcursors.cursor(sc, hover=True)

    @cursor.connect("add")
    def on_add(sel) -> None:
        sel.annotation.set_text(labels[sel.index])

    ax.set_title("Projection des votants")
    ax.set_aspect('equal', adjustable='box')
    plt.tight_layout()
    plt.show()


def affiche_graphe_3d() -> None:
    """Affiche un graphe 3D à partir du fichier coordonnes_3d.csv et des fichiers auxiliaires"""
    import pandas as pd
    import matplotlib.pyplot as plt
    import mplcursors
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    import plotly.graph_objects as go

    # lecture du fichier des coordonnées 3D
    embedding = pd.read_csv(COORDONNES_3D_FILE, sep=';', index_col=0)

    # Chargement des tables auxiliaires
    acteurs_groupe         = pd.read_csv(ACTEURS_FILE,    sep=';', header=None).set_index(0)[1].to_dict()
    acteurs_nom            = pd.read_csv(ACTEURS_FILE,    sep=';', header=None).set_index(0)[2].to_dict()
    acteurs_prenom         = pd.read_csv(ACTEURS_FILE,    sep=';', header=None).set_index(0)[3].to_dict()
    organes                = pd.read_csv(ORGANES_FILE,    sep=';', header=None).set_index(0)[2].to_dict()
    groupes_couleurs = pd.read_csv(GROUPES_COULEURS_FILE, sep=';', header=None).set_index(0)[3].to_dict()

    # Lecture du nombre de votes par acteur pour dimensionner les points
    participation = pd.read_csv(ACTEURS_PARTICIP_FILE, sep=';', index_col=0)
    vote_counts = participation['nombre_de_votes'].to_dict()

    votes = list(vote_counts.values())
    max_votes = max(votes) if votes else 1

    def point_size(act_id: str) -> int:
        nb_votes = vote_counts.get(act_id, 0)
        # return int(5.0 + 20 * math.sqrt((nb_votes / max_votes))) # tentative de taille proportionnelle à la participation
        return 10

    # construction du graphe 3D
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection='3d')

    xs = []
    ys = []
    zs = []
    colors = []
    sizes = []
    labels = []

    for acteur_id, row in embedding.iterrows():
        try:
            x = row['x']
            y = row['y']
            z = row['z']
            groupe_label = organes[acteurs_groupe[acteur_id]]
            acteur_couleur = groupes_couleurs[groupe_label]
            xs.append(x)
            ys.append(y)
            zs.append(z)
            colors.append(acteur_couleur)
            sizes.append(point_size(str(acteur_id)))
            labels.append(acteurs_prenom[acteur_id] + " " + acteurs_nom[acteur_id] + ", " + acteur_id + ", " + groupe_label)
        except (KeyError, TypeError, ValueError):
            continue

    sc = ax.scatter(xs, ys, zs, s=sizes, c=colors, depthshade=True)

    # ajout des étiquettes au survol à la souris
    cursor = mplcursors.cursor(sc, hover=True)

    @cursor.connect("add")
    def on_add(sel) -> None:
        try:
            sel.annotation.set_text(labels[sel.index])
        except (IndexError, TypeError, ValueError):
            sel.annotation.set_text("")

    ax.set_title("Projection 3D des votants")
    plt.tight_layout()

    # export du graphe 3D en HTML interactif
    hover_texts = labels
    trace = go.Scatter3d(
        x=xs,
        y=ys,
        z=zs,
        mode='markers',
        marker=dict(size=sizes, color=colors, opacity=0.8),
        text=hover_texts,
        hoverinfo='text'
    )

    layout = go.Layout(title='Projection 3D des votants', scene=dict(xaxis_title='x', yaxis_title='y', zaxis_title='z'))
    fig_plotly = go.Figure(data=[trace], layout=layout)

    html_name = 'projection_3d.html'
    fig_plotly.write_html(html_name, include_plotlyjs='cdn')
    print(f"Graphe 3D interactif sauvegardé en HTML : {html_name}")

    # Enfin afficher la figure matplotlib (interaction via souris locale)
    plt.show()


def main() -> None:
    while True:
        choix = input("VOTRE CHOIX : o: organes, v: votes, d: distances, s: statistiques, u: réduction UMAP 2D, u3: réduction UMAP 3D, m: réduction MDS 2D, m3: réduction MDS 3D, a: affiche graphe 2D, a3: affiche graphe 3D, q: quitter\n> ")
        
        match choix:
            case "o": calcul_organes()
            case "v": calcul_votes()
            case "d": calcul_distances()
            case "s": statistiques()
            case "u":
                # umap_2d()
                reduire('umap', n_components=2, n_neighbors=3, min_dist=0, random_state=42)
            case "u3":
                # umap_3d()
                reduire('umap', n_components=3, n_neighbors=15, min_dist=0.1, random_state=42)
            case "m":
                # mds_2d()
                reduire('mds', n_components=2, random_state=42)
            case "m3":
                # mds_3d()
                reduire('mds', n_components=3, random_state=42)
            case "a":
                affiche_graphe_2d()
            case "a3":
                affiche_graphe_3d()
            case "q":
                break
            case _: print("Choix invalide. Veuillez réessayer.")


if __name__ == "__main__":
    main()
