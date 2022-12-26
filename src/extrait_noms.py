
import re
import json
import pandas as pd

CORPUS = './corpus/lx_corpus.json'
LS_MARKER = ['un', 'une']

LS_ADJ_AVANT = ['beau', 'bon', 'bref', 'grand', 'gros', 'faux', 'haut', 'jeune', 'joli', 'mauvais', 'meilleur',
                'nouveau', 'petit', 'vieux',
                'bel', 'belle', 'bonne', ' grande', 'grosse', 'haute', 'jolie', 'mauvaise', 'meilleure',
                'nouvelle', 'petite', 'vielle',
                'ancien', 'ancienne', 'brave', 'certain', 'certaine', 'cher', 'chere', 'curieux', 'curieuse',
                'dernier', 'derniere', 'drole', 'pauvre', 'prochain', 'prochaine', 'propre', 'pur', 'pure',
                'sacre', 'sale', 'seul', 'seule', 'simple', 'vrai', 'vraie',
                'severe', 'immense', 'profond', 'profonde', 'tel', 'telle', 'meme', 'nécessaire' 'ou',
                'démence']


def has_digit(text):
    return bool(re.search(r'\d', text))

def is_nom(mot_next):
    is_nom = True
    if has_digit(mot_next) or mot_next.isupper() or (mot_next in LS_ADJ_AVANT):
        is_nom = False
    return is_nom

# ...   =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# ...   main()
# ...   =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


if __name__ == '__main__':

    with open(CORPUS, 'r') as f:
        lx_corpus = json.load(f)

    ls_nom = []
    ls_gndr = []
    ls_phrase = []

    for t in lx_corpus['text']:
        t = t.replace("’", " ")
        t = t.replace(",", " ")
        t = t.replace(".", " ")
        t = t.replace("“", " ")

        ls_mot = t.split()

        for indx, mot in enumerate(ls_mot):
            if mot.lower() in LS_MARKER:

                mot_next = ls_mot[indx+1]

                # filter out digits, acronyms, and preceding adjectives
                if is_nom(mot_next):
                    ls_nom.append(mot_next)
                    if mot.lower() == 'un':
                        ls_gndr.append('m')
                    else:
                        ls_gndr.append('f')

                    indx2 = min(indx+10, len(ls_mot))
                    ce_phrase = ' '.join(ls_mot[indx:indx2])
                    ls_phrase.append(ce_phrase)
                    print('%03d | %15s | %-80s' % (indx, mot_next, ce_phrase))

    df_nom = pd.DataFrame({'nom': ls_nom, 'gender': ls_gndr, 'phrase': ls_phrase})
    df_nom['score'] = 0
    df_nom['n'] = 0

    df_nom.drop_duplicates(inplace=True)
    df_nom.reset_index(inplace=True, drop=True)
    df_nom.sort_values(by='nom', inplace=True)

    # ... remove duplicate noms, retain phrases in list

    df_nom['nom_gndr'] = df_nom['nom'] + '_' + df_nom['gender']
    ls_nom_gndr = df_nom['nom_gndr'].unique().tolist()

    df_nom.to_csv('les_noms.csv', index=False)

