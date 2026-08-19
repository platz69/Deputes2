# bibliothèques standard
import os
import json

# entrées
ACTEURS_FOLDER        = "acteurs"              # dossier où l'on dépose les fichiers PAxxxx.json
ORGANES_FOLDER        = "organes"              # dossier où l'on dépose les fichiers POxxxx.json
SCRUTINS_FOLDER       = "scrutins"             # dossier où l'on dépose les fichiers VTANR5L16Vxxxx.json
GROUPES_COULEURS_FILE = "groupes_couleurs.csv" # id_groupe;libellé;couleur

# sorties
TEMP_FOLDER         = "temp"                   # dossier temporaire pour les fichiers intermédiaires
# créer le dossier temporaire s'il n'existe pas
os.makedirs(TEMP_FOLDER, exist_ok=True)

ACTEURS_GROUP_FILE  = os.path.join(TEMP_FOLDER, "acteurs_groupes.csv")    # id_acteur;id_groupe;nom;prenom
VOTES_FILE          = os.path.join(TEMP_FOLDER, "votes.csv")              # id_acteur;vote1;vote2;...;vote4000;...
DISTANCES_FILE      = os.path.join(TEMP_FOLDER, "distances.csv")          # id_acteur;distance_acteur1;distance_acteur2;distance_acteur3;...
COORDINATES_FILE    = os.path.join(TEMP_FOLDER, "coordinates.csv")        # id_acteur;x;y
COORDINATES_3D_FILE = os.path.join(TEMP_FOLDER, "coordinates_3d.csv")     # id_acteur;x;y;z
ORGANES_FILE        = os.path.join(TEMP_FOLDER, "organes.csv")            # id_organe;type_organe;libelle_abrev;libelle


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


def charger_noms_prenoms_acteurs():
    """Charge les noms et prénoms des acteurs depuis les fichiers JSON"""
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


def calcul_votes():

    # Dictionnaires
    votes_dict    = {}
    scrutins_list = []
    votant_dict   = {}

    # Charger les noms et prénoms des acteurs
    acteurs_info = charger_noms_prenoms_acteurs()

    # Parcourir les fichiers JSON du dossier Scrutins
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

        # Pour chaque votant, écrire une ligne avec son ID et ses votes
        for acteur_ref in sorted(votes_dict.keys()):
            row = [acteur_ref]
            for scrutin_uid in scrutins_list:
                vote_value = votes_dict[acteur_ref].get(scrutin_uid, '')
                row.append(str(vote_value) if vote_value != '' else '0')
            f.write(";".join(row) + "\n")

    # Créer le CSV des votants_groupe parlementaire avec noms et prénoms
    with open(ACTEURS_GROUP_FILE, "w", encoding="utf-8", newline='') as f:
        for acteur_ref in sorted(votes_dict.keys()):
            info = acteurs_info.get(acteur_ref, {'nom': '', 'prenom': ''})
            f.write(";".join([acteur_ref, votant_dict[acteur_ref], info['nom'], info['prenom']]) + "\n")


def calcul_distances():
    import numpy as np
    import pandas as pd

    # Lecture du fichier CSV, la première colonne est utilisée comme index
    df = pd.read_csv(VOTES_FILE, sep=';', index_col=0) # noqa

    deputes = df.index
    votes = df.to_numpy()
    nb_deputes = df.shape[0]

    # Matrice des distances
    dist = np.zeros((nb_deputes, nb_deputes), dtype=int)

    # Calcul des distances (même vote : +0, une abstention : +1, opposé : +2)
    for i in range(nb_deputes):
        for j in range(i, nb_deputes):
            d = np.sum(np.abs(votes[i,:] - votes[j,:]))
            dist[i, j] = d
            dist[j, i] = d

    # Sauvegarde du tableau des distances
    distance_df = pd.DataFrame(dist, index=deputes, columns=deputes)
    distance_df.to_csv(DISTANCES_FILE, sep=';')


def umap_2d(n_neighbors=3, min_dist=0, random_state=42):
    import pandas as pd
    import umap

    # Chargement du tableau des distances
    distances = pd.read_csv(DISTANCES_FILE, sep=';', index_col=0)

    # réduction en 2D avec UMAP
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

    # Arrondir les coordonnées à 2 décimales
    result = result.round(2)

    # Sauvegarde du fichier des coordonnées (2 décimales)
    result.to_csv(COORDINATES_FILE, sep=';', float_format='%.2f')


def umap_3d(n_neighbors=15, min_dist=0.1, random_state=42):
    import pandas as pd
    import umap

    # Chargement du tableau des distances
    distances = pd.read_csv(DISTANCES_FILE, sep=';', index_col=0)

    # réduction en 3D avec UMAP
    reducer = umap.UMAP(
        n_components=3,
        metric="precomputed",
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        random_state=random_state
    )

    reduc = reducer.fit_transform(distances)

    result = pd.DataFrame(
        reduc,
        index=distances.index,
        columns=["x", "y", "z"]
    )

    # Arrondir les coordonnées à 2 décimales
    result = result.round(2)

    # Sauvegarde du fichier des coordonnées 3D (2 décimales)
    result.to_csv(COORDINATES_3D_FILE, sep=';', float_format='%.2f')


def mds_2d(n_components=2, dissimilarity="precomputed", random_state=42):
    """
    Réduit une matrice de distances avec MDS (2D)
    """
    import pandas as pd
    from sklearn.manifold import MDS

    # Chargement du tableau des distances
    distances = pd.read_csv(DISTANCES_FILE, sep=';', header=0, index_col=0)

    # réduction en 2D avec MDS
    mds = MDS(
        n_components=n_components,
        dissimilarity=dissimilarity,
        random_state=random_state
    )

    coords = mds.fit_transform(distances.values)

    # Sauvegarde du fichier des coordonnées
    embedding = pd.DataFrame(
        coords,
        index=distances.index,
        columns=[f"MDS{i+1}" for i in range(n_components)]
    )

    # Arrondir les coordonnées à 2 décimales
    embedding = embedding.round(2)

    embedding.to_csv(COORDINATES_FILE, sep=';', float_format='%.2f')

    return


def mds_3d(n_components=3, dissimilarity="precomputed", random_state=42):
    """
    Réduit une matrice de distances avec MDS et produit coordinates_3d.csv (colonnes x;y;z)
    """
    import pandas as pd
    from sklearn.manifold import MDS

    # Chargement du tableau des distances
    distances = pd.read_csv(DISTANCES_FILE, sep=';', header=0, index_col=0)

    # réduction en 3D avec MDS
    mds = MDS(
        n_components=n_components,
        dissimilarity=dissimilarity,
        random_state=random_state
    )

    coords = mds.fit_transform(distances.values)

    # Sauvegarde du fichier des coordonnées 3D
    embedding = pd.DataFrame(
        coords,
        index=distances.index,
        columns=["x", "y", "z"]
    )

    # Arrondir les coordonnées à 2 décimales
    embedding = embedding.round(2)

    embedding.to_csv(COORDINATES_3D_FILE, sep=';', float_format='%.2f')

    return


def affiche_graphe_2d():
    import pandas as pd
    import matplotlib.pyplot as plt
    import mplcursors

    # lecture du fichier des coordonnées
    try:
        embedding = pd.read_csv(COORDINATES_FILE, sep=';', index_col=0)
    except FileNotFoundError:
        print(f"Fichier {COORDINATES_FILE} introuvable.")
        return
    except Exception as e:
        print(f"Erreur en lisant {COORDINATES_FILE} : {e}")
        return

    # Chargement des tables auxiliaires
    acteurs_groupes        = pd.read_csv(ACTEURS_GROUP_FILE,    sep=';', header=None).set_index(0)[1].to_dict()
    acteurs_nom            = pd.read_csv(ACTEURS_GROUP_FILE,    sep=';', header=None).set_index(0)[2].to_dict()
    acteurs_prenom         = pd.read_csv(ACTEURS_GROUP_FILE,    sep=';', header=None).set_index(0)[3].to_dict()
    organes                = pd.read_csv(ORGANES_FILE,          sep=';', header=None).set_index(0)[2].to_dict()
    groupes_abrev_couleurs = pd.read_csv(GROUPES_COULEURS_FILE, sep=';', header=None).set_index(0)[2].to_dict()

    # construction du graphe
    fig, ax = plt.subplots(figsize=(8, 8))

    xs = []
    ys = []
    colors = []
    labels = []

    for acteur_ref, (x, y) in embedding.iterrows():
        try:
            acteur_couleur = groupes_abrev_couleurs[organes[acteurs_groupes[acteur_ref]]]
            xs.append(x)
            ys.append(y)
            colors.append(acteur_couleur)
            labels.append(acteurs_prenom[acteur_ref] + " " + acteurs_nom[acteur_ref] + ", " + organes[acteurs_groupes[acteur_ref]])
        except Exception:
            # si un acteur manque dans les tables, on l'ignore
            continue

    sc = ax.scatter(xs, ys, s=80, color=colors)

    # ajout des étiquettes au survol à la souris
    cursor = mplcursors.cursor(sc, hover=True)

    @cursor.connect("add")
    def on_add(sel):
        sel.annotation.set_text(labels[sel.index])

    ax.set_title("Projection des votants")
    ax.set_aspect('equal', adjustable='box')
    plt.tight_layout()
    plt.show()


def affiche_graphe_3d():
    import pandas as pd
    import matplotlib.pyplot as plt
    import mplcursors
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    import plotly.graph_objects as go

    # lecture du fichier des coordonnées 3D
    try:
        embedding = pd.read_csv(COORDINATES_3D_FILE, sep=';', index_col=0)
    except FileNotFoundError:
        print(f"Fichier {COORDINATES_3D_FILE} introuvable.")
        return
    except Exception as e:
        print(f"Erreur en lisant {COORDINATES_3D_FILE} : {e}")
        return

    # Chargement des tables auxiliaires
    acteurs_groupes        = pd.read_csv(ACTEURS_GROUP_FILE,    sep=';', header=None).set_index(0)[1].to_dict()
    acteurs_nom            = pd.read_csv(ACTEURS_GROUP_FILE,    sep=';', header=None).set_index(0)[2].to_dict()
    acteurs_prenom         = pd.read_csv(ACTEURS_GROUP_FILE,    sep=';', header=None).set_index(0)[3].to_dict()
    organes                = pd.read_csv(ORGANES_FILE,          sep=';', header=None).set_index(0)[2].to_dict()
    groupes_abrev_couleurs = pd.read_csv(GROUPES_COULEURS_FILE, sep=';', header=None).set_index(0)[2].to_dict()

    # construction du graphe 3D
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection='3d')

    xs = []
    ys = []
    zs = []
    colors = []
    labels = []

    for acteur_ref, row in embedding.iterrows():
        try:
            x = row['x']
            y = row['y']
            z = row['z']
            acteur_couleur = groupes_abrev_couleurs[organes[acteurs_groupes[acteur_ref]]]
            xs.append(x)
            ys.append(y)
            zs.append(z)
            colors.append(acteur_couleur)
            labels.append(acteurs_prenom[acteur_ref] + " " + acteurs_nom[acteur_ref] + ", " + organes[acteurs_groupes[acteur_ref]])
        except Exception:
            continue

    sc = ax.scatter(xs, ys, zs, s=60, c=colors, depthshade=True)

    # ajout des étiquettes au survol à la souris
    cursor = mplcursors.cursor(sc, hover=True)

    @cursor.connect("add")
    def on_add(sel):
        # sel.index devrait correspondre à l'indice pointé
        try:
            sel.annotation.set_text(labels[sel.index])
        except Exception:
            sel.annotation.set_text("")

    ax.set_title("Projection 3D des votants")
    plt.tight_layout()

    # export du graphe 3D en HTML interactif
    try:
        hover_texts = labels
        trace = go.Scatter3d(
            x=xs,
            y=ys,
            z=zs,
            mode='markers',
            marker=dict(size=4, color=colors, opacity=0.8),
            text=hover_texts,
            hoverinfo='text'
        )

        layout = go.Layout(title='Projection 3D des votants', scene=dict(xaxis_title='x', yaxis_title='y', zaxis_title='z'))
        fig_plotly = go.Figure(data=[trace], layout=layout)

        html_name = 'projection_3d.html'
        fig_plotly.write_html(html_name, include_plotlyjs='cdn')
        print(f"Graphe 3D interactif sauvegardé en HTML : {html_name}")
    except Exception as e:
        print(f"Plotly non disponible ou erreur export HTML : {e}")

    # Enfin afficher la figure matplotlib (interaction via souris locale)
    plt.show()


def main():
    while True:
        choix = input("VOTRE CHOIX : o: organes, v: votes, d: distances, u: réduction UMAP 2D, u3: réduction UMAP 3D, m: réduction MDS 2D, m3: réduction MDS 3D, a: affiche graphe 2D, a3: affiche graphe 3D, q: quitter\n> ")
        
        match choix:
            case "o": calcul_organes()
            case "v": calcul_votes()
            case "d": calcul_distances()
            case "u":
                umap_2d()
            case "u3":
                umap_3d()
            case "m":
                mds_2d()
            case "m3":
                mds_3d()
            case "a":
                affiche_graphe_2d()
            case "a3":
                affiche_graphe_3d()
            case "q":
                break
            case _: print("Choix invalide. Veuillez réessayer.")


if __name__ == "__main__":
    main()
