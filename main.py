# bibliothèques standard
import math  # uniquement pour la racine carrée sqrt() !
import os
import json

# bibliothèques tierces communes
import pandas as pd
from typing import Any, Dict, Hashable, Union

# entrées
ACTEURS_FOLDER         = 'acteur'               # répertoire où l'on dépose les fichiers PAxxxx.json
ORGANES_FOLDER         = 'organe'               # répertoire où l'on dépose les fichiers POxxxx.json
SCRUTINS_FOLDER        = 'scrutin'              # répertoire où l'on dépose les fichiers VTANR5LxxVxxxx.json

# paramètres
TENDANCES_COULEUR_FILE = 'abrev_libel_tendance_couleur.csv' # abrev;libelle;tendance;couleur

# sorties
TEMP_FOLDER = 'temp'  # répertoire temporaire pour les fichiers CSV intermédiaires
os.makedirs(TEMP_FOLDER, exist_ok=True)

# fichiers à nb de colonnes fixe
ACTEURS_FILE                     = os.path.join(TEMP_FOLDER, 'acteur_groupe_nom_prenom.csv')   # 'acteur_id;groupe_id;nom;prenom'
ACTEURS_PARTICIP_FILE            = os.path.join(TEMP_FOLDER, 'acteur_particip.csv')            # 'acteur_id;nb_votes'
ACTEUR_TENDANCE_RELLE            = os.path.join(TEMP_FOLDER, 'acteur_tendance_reelle.csv')     # 'acteur_id;tendance;tendance'
ACTEUR_LABEL_FILE                = os.path.join(TEMP_FOLDER, 'acteur_label.csv')               # 'acteur_id;label'
ACTEURS_X_Y_FILE                 = os.path.join(TEMP_FOLDER, 'acteur_x_y.csv')                 # 'id_acteur;x;y'
ACTEURS_X_Y_Z_FILE               = os.path.join(TEMP_FOLDER, 'acteur_x_y_z.csv')               # 'id_acteur;x;y;z'
GROUPES_ABREV_LIBELLE_FILE       = os.path.join(TEMP_FOLDER, 'groupe_abrev_libelle.csv')       # 'groupe_id;abrev;libelle'

# fichiers à nb de colonnes variable
ACTEUR_VOTE_FILE                 = os.path.join(TEMP_FOLDER, 'acteur_vote.csv')                # acteur_id   vs scrutin_id
TENDANCE_VOTE_FILE               = os.path.join(TEMP_FOLDER, 'tendance_vote.csv')              # tendance_id vs scrutin_id
DISTANCES_ACTEUR_ACTEUR_FILE     = os.path.join(TEMP_FOLDER, 'distance_acteur_acteur.csv')     # 'acteur_id  vs acteur_id'
DISTANCES_ACTEUR_TENDANCE_FILE   = os.path.join(TEMP_FOLDER, 'distance_acteur_tendance.csv')   # 'acteur_id  vs libelle'
DISTANCES_TENDANCE_TENDANCE_FILE = os.path.join(TEMP_FOLDER, 'distance_tendance_tendance.csv') # 'libelle    vs libelle'

# couleurs d'affichage dans la console
blue, green = '\033[34m', '\033[32m'
reset = '\033[0m'


def charger_votes() -> pd.DataFrame:
    return pd.read_csv(ACTEUR_VOTE_FILE, sep=';', index_col=0)


def charger_distances() -> pd.DataFrame:
    return pd.read_csv(DISTANCES_ACTEUR_ACTEUR_FILE, sep=';', index_col=0)


def calcul_groupes() -> None:
    """Produit le fichier GROUPES_FILE à partir des fichiers JSON du répertoire ORGANES_FOLDER"""

    # ouverture du fichier GROUPES_FILE en écriture
    with open(GROUPES_ABREV_LIBELLE_FILE, 'w', encoding='utf-8', newline='') as groupe_file:
        groupe_file.write('groupe_id;abrev;libelle\n')

        # Parcourir les fichiers JSON du répertoire ORGANES_FOLDER
        for file in sorted(os.listdir(ORGANES_FOLDER)):
            if file.endswith('.json'):
                json_path = os.path.join(ORGANES_FOLDER, file)
                with open(json_path, encoding='utf-8') as f:
                    data = json.load(f)
                    type_organe = data['organe']['codeType']
                    # on ne cherche que les groupes parlementaires
                    if type_organe == 'GP':
                        groupe_id = data['organe']['uid']
                        abrev     = str(data['organe']['libelleAbrev']).upper()
                        libelle   = data['organe']['libelle']
                        groupe_file.write(';'.join([groupe_id, abrev, libelle]) + '\n')


def charger_dossier_acteur() -> Dict[str, Dict[str, str]]:
    """Charge les noms et prénoms de TOUS les acteurs depuis le répertoire ACTEURS_FOLDER
    et retourne un dictionnaire {acteur_uid: {'nom': nom, 'prenom': prenom}}"""

    acteurs_info = {}

    for file in sorted(os.listdir(ACTEURS_FOLDER)):
        if file.endswith('.json'):
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


def calcul_acteurs_et_votes() -> None:
    """Produit les fichiers DISTANCES_ACTEUR_ACTEUR_FILE et ACTEURS_FILE à partir des fichiers JSON du répertoire scrutins"""

    # Dictionnaires
    votant_dict = {}
    votes_dict = {}
    scrutins_list = []

    # Charge les noms et prénoms des acteurs
    acteurs_info = charger_dossier_acteur()

    # Parcourir les fichiers JSON du répertoire scrutins
    for file in sorted(os.listdir(SCRUTINS_FOLDER)):
        if file.endswith('.json') and file.startswith(
                'VTA'):  # attention il y a un fichier VTCxxx à éviter, on ne prend que les VTAxxx !
            scrutin_id = file.replace('.json', '')
            scrutins_list.append(scrutin_id)

            json_path = os.path.join(SCRUTINS_FOLDER, file)
            with open(json_path, encoding='utf-8') as f:
                data = json.load(f)
                groups = data['scrutin']['ventilationVotes']['organe']['groupes']['groupe']

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
    with open(ACTEUR_VOTE_FILE, 'w', encoding='utf-8', newline='') as f:
        # En-tête avec les UIDs des scrutins
        header = [''] + scrutins_list
        f.write(';'.join(header) + '\n')

        # Pour chaque votant, écrire une ligne avec son ID et ses votes
        for acteur_id in sorted(votes_dict.keys()):
            row = [acteur_id]
            for scrutin_uid in scrutins_list:
                vote_value = votes_dict[acteur_id].get(scrutin_uid, '')
                row.append(str(vote_value) if vote_value != '' else '0')
            f.write(';'.join(row) + '\n')

    # Créer le fichier ACTEURS_FILE avec en-tête
    with open(ACTEURS_FILE, 'w', encoding='utf-8', newline='') as f:
        f.write('acteur_id;groupe_id;nom;prenom\n')
        for acteur_id in sorted(votes_dict.keys()):
            info = acteurs_info.get(acteur_id, {'nom': '', 'prenom': ''})
            f.write(';'.join([acteur_id, votant_dict[acteur_id], info['nom'], info['prenom']]) + '\n')


def calcul_tendance_vote():
    """Calcule la somme des votes (-1, 0, +1) par tendance ET par scrutin

    Parcourt TABLE_VOTES_FILE (index = acteur_id, colonnes = scrutins) et utilise
    ACTEURS_FILE, GROUPES_FILE et TENDANCES_COULEUR_FILE pour mapper chaque
    acteur à sa tendance. Écrit le résultat dans GROUPES_VOTE_FILE (CSV) et
    retourne le DataFrame (index=tendance, colonnes=scrutins).
    """

    # lecture du tableau des votes
    df_votes = pd.read_csv(ACTEUR_VOTE_FILE, sep=';', index_col=0)

    # conversion en valeurs numériques (-1/0/1), remplacer valeurs manquantes par 0
    df_num = df_votes.apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)

    # chargement des mappings pour retrouver la tendance d'un acteur
    acteurs_groupes = charger_csv(ACTEURS_FILE)['groupe_id']  # acteur_id -> organe_id
    groupes_abrev = charger_csv(GROUPES_ABREV_LIBELLE_FILE)                 # organe_id -> abrev
    groupes_tendance = pd.read_csv(TENDANCES_COULEUR_FILE, sep=';').set_index('abrev')['tendance'].to_dict()

    # construire une Series mapping index acteur -> tendance (alignée sur df_num.index)
    tendances = []
    for acteur_id in df_num.index:
        aid = str(acteur_id)
        grp = acteurs_groupes.get(aid)
        abrev = groupes_abrev.get(grp)
        tend = groupes_tendance.get(abrev) if abrev is not None else None
        if not tend:
            tend = 'Inconnu'
        tendances.append(tend)

    s_tendance = pd.Series(tendances, index=df_num.index)

    # grouper par tendance et sommer par scrutin
    df_somme = df_num.groupby(s_tendance).sum()

    # normaliser chaque cellule à -1 / 0 / +1 pour représenter la direction du vote
    df_norm = df_somme.map(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

    # Écriture du CSV GROUPES_VOTE_FILE (valeurs normalisées)
    try:
        df_norm.to_csv(TENDANCE_VOTE_FILE, sep=';', index=True)
    except Exception as e:
        print(f"Erreur écriture {TENDANCE_VOTE_FILE}: {e}")

    return df_norm

def calcul_distances_acteurs() -> None:
    """ Produit le fichier DISTANCES_ACTEUR_ACTEUR_FILE à partir du fichier TABLE_VOTES_FILE """
    import numpy as np

    # Lecture du fichier CSV, la première colonne est utilisée comme index
    df = charger_votes()  # noqa

    deputes = df.index
    votes = df.to_numpy()
    nb_deputes = df.shape[0]

    # Initialisation de la matrice des distances avec des zéros
    dist = np.zeros((nb_deputes, nb_deputes), dtype=int)

    # Calcul des distances (même vote : +0, une abstention : +1, opposé : +2)
    for i in range(nb_deputes):
        # la matrice est symétrique, on ne parcourt que la moitié supérieure
        for j in range(i, nb_deputes):
            d = np.sum(np.abs(votes[i, :] - votes[j, :]))
            dist[i, j] = d
            dist[j, i] = d

    # Sauvegarde du tableau des distances
    distance_df = pd.DataFrame(dist, index=deputes, columns=deputes)
    distance_df.to_csv(DISTANCES_ACTEUR_ACTEUR_FILE, sep=';')


def calcul_distances_acteurs_tendance() -> None:
    """Produit DISTANCES_ACTEUR_TENDANCE_FILE à partir de TABLE_VOTES_FILE et TENDANCES_VOTE_FILE
    et chaque tendance.
    """
    import numpy as np

    df_acteurs = pd.read_csv(ACTEUR_VOTE_FILE, sep=';', index_col=0)
    df_tendances = pd.read_csv(TENDANCE_VOTE_FILE, sep=';', index_col=0)

    # mais çasert à riença !  et dasn la def precedente ?
    df_a = df_acteurs.apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
    df_t = df_tendances.apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)

    votes_acteurs = df_a.to_numpy()
    votes_tendances = df_t.to_numpy()

    # Broadcasting : (n_acteurs, 1, n_cols) - (1, n_tendances, n_cols) -> (n_acteurs, n_tendances)
    dist = np.abs(votes_acteurs[:, None, :] - votes_tendances[None, :, :]).sum(axis=2)

    distance_df = pd.DataFrame(dist, index=df_a.index.astype(str), columns=df_t.index.astype(str))
    distance_df.to_csv(DISTANCES_ACTEUR_TENDANCE_FILE, sep=';')


def charger_fichier_acteur() -> Dict[str, Dict[str, str]]:
    """Charge les noms et prénoms des acteurs depuis ACTEURS_FILE (produit par calcul_acteurs_et_votes())
    et retourne un dictionnaire {acteur_uid: {'nom': nom, 'prenom': prenom}}"""

    df = pd.read_csv(ACTEURS_FILE, sep=';', dtype=str).set_index('acteur_id')
    return {str(acteur_id): {'nom': str(row['nom']), 'prenom': str(row['prenom'])}
            for acteur_id, row in df.iterrows()}


def acteur_tendance_relle() -> None:
    """Produit le fichier ACTEUR_TENDANCE_RELLE (en-tête 'acteur_id;groupe_id;groupe_reel_id')

    Pour chaque acteur :
    - retrouve son groupe déclaré via ACTEURS_FILE (colonne 'groupe_id'),
    - retrouve l'abréviation de ce groupe via GROUPES_ABREV_LIBELLE_FILE,
    - en déduit sa tendance déclarée via TENDANCES_COULEUR_FILE,
    - puis la rapproche de la tendance dont il est réellement le plus proche
      d'après DISTANCES_ACTEUR_TENDANCE_FILE (distance minimale = tendance la plus proche).
    """

    acteurs_groupes = charger_csv(ACTEURS_FILE)['groupe_id']
    groupes_abrev = charger_csv(GROUPES_ABREV_LIBELLE_FILE)
    groupes_tendance = pd.read_csv(TENDANCES_COULEUR_FILE, sep=';').set_index('abrev')['tendance'].to_dict()
    df_distances = pd.read_csv(DISTANCES_ACTEUR_TENDANCE_FILE, sep=';', index_col=0)
    df_distances.index = df_distances.index.astype(str)

    # tendance réellement la plus proche = colonne de distance minimale
    tendance_reelle = df_distances.idxmin(axis=1)

    # Écriture du fichier ACTEUR_TENDANCE_RELLE
    with open(ACTEUR_TENDANCE_RELLE, 'w', encoding='utf-8', newline='') as f:
        f.write('acteur_id;groupe_id;groupe_reel_id\n')
        for acteur_id in df_distances.index:
            grp = acteurs_groupes.get(acteur_id)
            abrev = groupes_abrev.get(grp)
            tendance_declaree = groupes_tendance.get(abrev) if abrev is not None else None
            if not tendance_declaree:
                tendance_declaree = 'Inconnu'
            groupe_reel_id = tendance_reelle.get(acteur_id, 'Inconnu')
            f.write(f'{acteur_id};{tendance_declaree};{groupe_reel_id}\n')


def calcul_participation() -> None:
    """Produit le fichier ACTEURS_PARTICIP_FILE
    """

    df = charger_votes()

    # Convertir en numérique et remplacer les non-nombres par 0
    df_num = df.apply(pd.to_numeric, errors='coerce').astype(int).fillna(0)

    # Participation = somme des valeurs non-nulles de la ligne
    participation = (df_num != 0).sum(axis=1)

    # Écriture du fichier ACTEURS_PARTICIP_FILE
    with open(ACTEURS_PARTICIP_FILE, 'w', encoding='utf-8', newline='') as f:
        f.write('acteur_id;nb_votes\n')
        for acteur, count in participation.items():
            f.write(f'{acteur};{count}\n')


def charger_csv(fichier: str) -> Union[Dict[Hashable, Any], Dict[str, Dict[Hashable, Any]]]:
    """Charge une table auxiliaire CSV (';') et la retourne sous forme de dict.
    - table à une seule colonne de valeur  -> {index_col: value_col}
    - table à plusieurs colonnes de valeur -> {colonne: {index_col: colonne}, ...}
      (dict de dicts ; ACTEURS_FILE est alors relu une fois par colonne)

    Attention DISTANCES_ACTEUR_ACTEUR_FILE et TABLE_VOTES_FILE ne doivent pas être chargés avec cette fonction
    car pas structurés de la même façon
    """
    if fichier == ACTEURS_FILE:
        return {col: pd.read_csv(ACTEURS_FILE, sep=';').set_index('acteur_id')[col].to_dict()
                for col in ['groupe_id', 'nom', 'prenom']}
    elif fichier == GROUPES_ABREV_LIBELLE_FILE:
        return pd.read_csv(GROUPES_ABREV_LIBELLE_FILE, sep=';').set_index('groupe_id')['abrev'].to_dict()
    elif fichier == TENDANCES_COULEUR_FILE:
        return pd.read_csv(TENDANCES_COULEUR_FILE, sep=';').set_index('abrev')['couleur'].to_dict()
    elif fichier == ACTEUR_LABEL_FILE:
        return pd.read_csv(ACTEUR_LABEL_FILE, sep=';').set_index('acteur_id')['label'].to_dict()
    elif fichier == ACTEURS_PARTICIP_FILE:
        return pd.read_csv(ACTEURS_PARTICIP_FILE, sep=';').set_index('acteur_id')['nb_votes'].to_dict()
    else:
        raise ValueError(f'table auxiliaire inconnue : {fichier}')


def statistiques() -> None:
    """Affiche des statistiques de participation des acteurs.
    """

    acteurs_info     = charger_fichier_acteur()
    acteurs_groupes  = charger_csv(ACTEURS_FILE)['groupe_id']
    groupes_abrev    = charger_csv(GROUPES_ABREV_LIBELLE_FILE)
    acteurs_particip = charger_csv(ACTEURS_PARTICIP_FILE)

    # participation : séries pandas (index=acteur_id -> nb_votes) — lu depuis ACTEURS_PARTICIP_FILE
    participation = pd.Series(acteurs_particip).astype(int)
    top5    = participation.sort_values(ascending=False).head(5)
    bottom5 = participation.sort_values(ascending=True).head(5)

    def acteur_label(acteur_id: str) -> str:
        """Retourne la chaîne 'prénom+nom+acteur_id+(groupe)+nb_votes'."""

        prenom    = acteurs_info[acteur_id]['prenom']
        nom       = acteurs_info[acteur_id]['nom']
        grp_id    = acteurs_groupes.get(acteur_id)
        grp_label = groupes_abrev.get(grp_id) or ''
        nb_votes  = acteurs_particip.get(acteur_id) or 0

        return prenom + ' ' + nom + ' ' + acteur_id + ' (' + grp_label + ') ' + str(nb_votes) + ' votes'

    print(blue + 'Top 5 des participants:' + reset)
    for i, (acteur, count) in enumerate(top5.items(), start=1):
        print(f'{i}. {acteur_label(str(acteur))}: {count}')

    print(blue + 'Top 5 des absents:' + reset)
    for i, (acteur, count) in enumerate(bottom5.items(), start=1):
        print(f'{i}. {acteur_label(str(acteur))}: {count}')

    # Calculer les paires les plus proches/éloignées à partir de DISTANCES_ACTEUR_ACTEUR_FILE
    distances_df = charger_distances()

    # ne pas tenir compte des acteurs n'ayant jamais voté pour ou contre qq chose
    actors = [a for a in distances_df.index if (acteurs_particip.get(str(a)) or 0) > 0]
    n = len(actors)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):  # on ne prend que la moitié supérieure de cette matrice symétrique
            d = distances_df.loc[actors[i], actors[j]]
            pairs.append((actors[i], actors[j], d))

    pairs_sorted = sorted(pairs, key=lambda t: t[2])
    closest5 = pairs_sorted[:5]
    farthest5 = pairs_sorted[-5:][::-1]

    print(blue + '\n5 paires les plus proches (distance la plus petite):' + reset)
    for i, (a, b, d) in enumerate(closest5, start=1):
        print(f'{i}. {acteur_label(str(a))}  -  {acteur_label(str(b))} : {d}')

    print(blue + '\n5 paires les plus éloignées (distance la plus grande):' + reset)
    for i, (a, b, d) in enumerate(farthest5, start=1):
        print(f'{i}. {acteur_label(str(a))}  -  {acteur_label(str(b))} : {d}')


def calcul_labels() -> None:

    acteurs_info = charger_fichier_acteur()
    acteurs_groupes = charger_csv(ACTEURS_FILE)['groupe_id']
    groupes_abrev = charger_csv(GROUPES_ABREV_LIBELLE_FILE)
    acteurs_particip = charger_csv(ACTEURS_PARTICIP_FILE)

    with open(ACTEUR_LABEL_FILE, 'w', encoding='utf-8', newline='') as f:
        f.write('acteur_id;label\n')
        # Parcours des acteurs ayant participé à cette législature
        for acteur_id in acteurs_particip:
            acteur_id = str(acteur_id)
            prenom = acteurs_info[acteur_id]['prenom']
            nom = acteurs_info[acteur_id]['nom']
            grp_id = acteurs_groupes.get(acteur_id)
            grp_label = groupes_abrev.get(grp_id) or ''
            nb_votes = acteurs_particip.get(acteur_id) or 0

            f.write(str(acteur_id) + ';' + prenom + ' ' + nom + ' ' + acteur_id + ' (' + grp_label + ') ' + str(
                nb_votes) + ' votes\n')


def reduire(algo: str, n_components: int, **kwargs) -> None:
    """Produit ACTEURS_X_Y (2D) ou ACTEURS_X_Y_Z (3D) via UMAP ou MDS"""

    distances = charger_distances()

    if algo == 'umap':
        import umap
        reducer = umap.UMAP(n_components=n_components, metric='precomputed', **kwargs)
    elif algo == 'mds':
        from sklearn.manifold import MDS
        reducer = MDS(n_components=n_components, dissimilarity='precomputed', **kwargs)
    else:
        raise ValueError(f'algo inconnu: {algo}')

    coords = reducer.fit_transform(distances)
    columns = ['x', 'y'] if n_components == 2 else ['x', 'y', 'z']
    result = pd.DataFrame(coords, index=distances.index, columns=columns).round(2)

    out_file = ACTEURS_X_Y_FILE if n_components == 2 else ACTEURS_X_Y_Z_FILE
    result.to_csv(out_file, sep=';', float_format='%.2f')


def affiche_graphe_2d() -> None:
    """Affiche un graphe 2D à partir du fichier ACTEURS_X_Y et des fichiers auxiliaires"""
    import matplotlib.pyplot as plt
    import mplcursors

    # lecture du fichier des coordonnées
    embedding = pd.read_csv(ACTEURS_X_Y_FILE, sep=';', index_col=0)

    # Chargement des tables auxiliaires
    acteurs_groupes    = charger_csv(ACTEURS_FILE)['groupe_id']
    groupes            = charger_csv(GROUPES_ABREV_LIBELLE_FILE)
    tendance_couleur   = charger_csv(TENDANCES_COULEUR_FILE)
    # acteur_labels    = charger_csv(ACTEUR_LABEL_FILE)
    # acteurs_particip = charger_csv(ACTEURS_PARTICIP_FILE)

    # # Calcul de la taille des points en fonction du nb de votes
    # votes = list(vote_counts.values())
    # min_votes = min(votes) if votes else 0
    # max_votes = max(votes) if votes else 1
    # def point_size(act_id: str) -> float:
    #     nb_votes = vote_counts.get(act_id, min_votes)
    #     return 80 if max_votes == min_votes else 20 + 200 * (nb_votes - min_votes) / (max_votes - min_votes)

    # construction du graphe
    fig, ax = plt.subplots(figsize=(8, 8))
    xs, ys, colors, sizes, labels = [], [], [], [], []

    for acteur_id, (x, y) in embedding.iterrows():
        try:
            groupe_label = groupes[acteurs_groupes[acteur_id]]
            acteur_couleur = tendance_couleur[groupe_label]
            xs.append(x)
            ys.append(y)
            colors.append(acteur_couleur)
            # sizes.append(point_size(str(acteur_id))) # taille de points variable
            labels.append(10)
        except (KeyError, TypeError, ValueError):
            # si un acteur manque dans les tables, on l'ignore
            continue

    sc = ax.scatter(xs, ys, s=sizes, color=colors)

    # ajout des étiquettes au survol à la souris
    cursor = mplcursors.cursor(sc, hover=True)

    @cursor.connect('add')
    def on_add(sel) -> None:
        sel.annotation.set_text(labels[sel.index])

    ax.set_title('Projection des votants')
    ax.set_aspect('equal', adjustable='box')
    plt.tight_layout()
    plt.show()


def affiche_graphe_3d() -> None:
    """Affiche un graphe 3D à partir du fichier ACTEURS_X_Y_Z et des fichiers auxiliaires"""
    import matplotlib.pyplot as plt
    import mplcursors
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    import plotly.graph_objects as go

    # lecture du fichier des coordonnées 3D
    embedding = pd.read_csv(ACTEURS_X_Y_Z_FILE, sep=';', index_col=0)

    # Chargement des tables auxiliaires
    acteurs_maps = charger_csv(ACTEURS_FILE)
    acteurs_groupe = acteurs_maps['groupe_id']
    acteurs_nom = acteurs_maps['nom']
    acteurs_prenom = acteurs_maps['prenom']
    groupes = charger_csv(GROUPES_ABREV_LIBELLE_FILE)
    tendance_couleur = charger_csv(TENDANCES_COULEUR_FILE)
    acteur_labels = charger_csv(ACTEUR_LABEL_FILE)

    # # Calcul de la taille des points
    # acteurs_particip = pd.read_csv(ACTEURS_PARTICIP_FILE, sep=';').set_index('acteur_id')['nb_votes'].to_dict()
    # votes = list(vote_counts.values())
    # max_votes = max(votes) if votes else 1
    # def point_size(act_id: str) -> int:
    #     # nb_votes = acteurs_particip.get(act_id, 0)
    #     # return int(5.0 + 20 * math.sqrt((nb_votes / max_votes))) # tentative de taille proportionnelle à la participation
    #     return 20

    # construction du graphe 3D
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection='3d')

    xs, ys, zs, colors, sizes, labels = [], [], [], [], [], []

    for acteur_id, row in embedding.iterrows():
        try:
            x = row['x']
            y = row['y']
            z = row['z']
            groupe_label = groupes[acteurs_groupe[acteur_id]]
            acteur_couleur = tendance_couleur[groupe_label]
            xs.append(x)
            ys.append(y)
            zs.append(z)
            colors.append(acteur_couleur)
            # sizes.append(point_size(str(acteur_id))) # taille de points variable
            sizes.append(10)
            labels.append(acteur_labels.get(str(acteur_id), acteurs_prenom[acteur_id] + ' ' + acteurs_nom[
                acteur_id] + ', ' + acteur_id + ', ' + groupe_label))
        except (KeyError, TypeError, ValueError):
            continue

    sc = ax.scatter(xs, ys, zs, s=sizes, c=colors, depthshade=True)

    # ajout des étiquettes au survol à la souris
    cursor = mplcursors.cursor(sc, hover=True)

    @cursor.connect('add')
    def on_add(sel) -> None:
        try:
            sel.annotation.set_text(labels[sel.index])
        except (IndexError, TypeError, ValueError):
            sel.annotation.set_text('')

    ax.set_title('Projection 3D des votants')
    # labels des axes pour la vue matplotlib 3D
    try:
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
    except Exception:
        # certains backends ou versions peuvent ne pas supporter set_zlabel proprement
        pass

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
    print(f'Graphe 3D interactif sauvegardé en HTML : {html_name}')

    # Enfin afficher la figure matplotlib (interaction via souris locale)
    plt.show()



def main() -> None:
    while True:
        choix = input('VOTRE CHOIX : ' \
                      + green + 'g' + reset + ': groupes, ' \
                      + green + 'v' + reset + ': votes, ' \
                      + green + 'd' + reset + ': distances, ' \
                      + green + 'p' + reset + ': participation, ' \
                      # + green + 's' + reset + ': statistiques, ' \
                      + green + 'l' + reset + ': labels, ' \
                      # + green + 'u' + reset + ': réduction UMAP 2D, ' \
                      # + green + 'u3' + reset + ': réduction UMAP 3D, ' \
                      # + green + 'm' + reset + ': réduction MDS 2D, ' \
                      + green + 'm3' + reset + ': réduction MDS 3D, ' \
                      + green + 'a' + reset + ': affiche graphe 2D, ' \
                      + green + 'a3' + reset + ': affiche graphe 3D, ' \
                      + green + 'i' + reset + ': traitement intégral 3D, ' \
                      + green + 'x' + reset + ': fonction test, '\
                      + green + 'q' + reset + ': quitter\
                      > ')

        match choix.lower():
            case 'o':
                calcul_groupes()
            case 'v':
                calcul_acteurs_et_votes()
            case 't':
                calcul_tendance_vote()
            case 'd':
                calcul_distances_acteurs()
            case 'p':
                calcul_participation()
            case 's':
                statistiques()
            case 'l':
                calcul_labels()
            # case 'u':
            #     # umap_2d()
            #     reduire('umap', n_components=2, n_neighbors=3, min_dist=0, random_state=42)
            # case 'u3':
            #     # umap_3d()
            #     reduire('umap', n_components=3, n_neighbors=15, min_dist=0.1, random_state=42)
            # case 'm':
            #     # mds_2d()
            #     reduire('mds', n_components=2, random_state=42)
            case 'm3':
                # mds_3d()
                reduire('mds', n_components=3, random_state=42)
            case 'a':
                affiche_graphe_2d()
            case 'a3':
                affiche_graphe_3d()
                break
            case 'i':
                calcul_groupes()
                calcul_acteurs_et_votes()
                calcul_tendance_vote()
                calcul_distances_acteurs()
                calcul_distances_acteurs_tendance()
                calcul_participation()
                statistiques()
                calcul_labels()
                reduire('mds', n_components=3, random_state=42)
                affiche_graphe_3d()
                break
            case 'x':
                acteur_tendance_relle()
            case 'q':
                break
            case _:
                print('Choix invalide. Veuillez réessayer.')


if __name__ == '__main__':
    main()
