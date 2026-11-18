# TD OpenSearch · déroulé de la séance (samedi 21 novembre)

**Objectif de fin de séance** : vous avez indexé un corpus de comptes rendus, écrit des requêtes plein texte,
comparé deux analyseurs, et construit une cohorte « patients diabétiques » qui écarte les négations et les
antécédents familiaux.

Les numéros de partie sont ceux des slides. Tout le code se fait dans **`seance3_etudiant.ipynb`** : les cellules
marquées `# À COMPLÉTER` sont à écrire, les autres s'exécutent telles quelles, dans l'ordre.

| Moment | Partie | Ce que vous faites | Vous avez fini quand… |
|---|---|---|---|
| 8 h 00 | Introduction | Lancer l'installation (README) pendant l'introduction | la première cellule du notebook affiche « OpenSearch 3.8.0 » |
| ≈ 8 h 45 | 01 · Moteurs plein texte | Exercice : votre index inversé, en Python (6 min) | vous savez pourquoi « décompensation » ne trouve pas la phrase 1 |
| ≈ 9 h 40 | 02 · Indexer et interroger | **TP requêtes** dans le notebook (15 min) | les cinq étapes donnent les chiffres ci-dessous |
| 10 h 10 | 03 · Analyse et agrégations | Suivre la partie 03 du notebook avec le cours | vous expliquez les écarts du tableau de comparaison |
| ≈ 11 h 30 | 04 · Pertinence et sens | Négation avec EDS-NLP, puis la cohorte | la cohorte compte 153 comptes rendus |

---

## Introduction · Installer (8 h 00)

Suivez le [README](README.md) : voie A (Docker) ou voie B (Codespaces). L'installation tourne pendant
l'introduction ; revenez-y à la fin de la partie 01 si elle n'a pas fini.

## Partie 01 · Votre index inversé (≈ 8 h 45, 6 min)

Partie 01 du notebook, en Python seulement : OpenSearch n'a pas besoin d'être prêt. Complétez la boucle qui
construit l'index des trois phrases de la slide, puis exécutez la recherche.

| Recherche | Phrases trouvées | Pourquoi |
|---|---|---|
| cardiaque | 1 et 3 | le mot est identique dans les deux |
| décompensation | 3 seulement | « décompensée » (phrase 1) est un autre terme dans l'index : pas de racine |
| insuffisance | 1 seulement | « d'insuffisance » (phrase 2) est resté collé : pas d'élision |

Si votre Python n'est pas encore installé, faites-le à la main sur la slide.

## Partie 02 · TP requêtes (≈ 9 h 40, 15 min)

Exécutez le notebook depuis le début, jusqu'à la fin de la partie 02.

| Étape | À écrire | Ce qu'on doit voir |
|---|---|---|
| Corpus | rien | 600 comptes rendus, 215 patients ; la cardiologie en tête |
| 1 · Indexer | `helpers.bulk` + `refresh` | `600 documents indexés` |
| 2 · Compter | `match`, puis `match_phrase` sur « insuffisance cardiaque » | 344 avec `match`, 119 avec `match_phrase` |
| 3 · Restreindre | `bool` : l'expression dans `must`, service et date dans `filter` | 11 comptes rendus de cardiologie en 2026 |
| Piège | rien | `term` sur un champ `text` : 0 ; `match` : 193 |
| 4 · Fautes de frappe | `match` avec `fuzziness: AUTO` sur « diabete » | 241 documents ; « diabéte », « diabte », « diabètte »… mais aussi « diététique » et « diurétiques » |
| 5 · Les plus récents | `sort` sur `date_creation` décroissant | le premier date du 11 octobre 2026 (CR0054) |

Une erreur `Unable to serialize Ellipsis` veut dire qu'il reste des `...` à remplacer dans la cellule.

**À retenir** : `match` cherche des mots, `match_phrase` une expression ; un filtre ne change pas le score ;
le flou rattrape les fautes de frappe, mais ramène aussi des mots voisins.

## Partie 03 · Analyse du texte et agrégations (10 h 10 – 11 h 00)

Suivez la partie 03 du notebook en même temps que le cours.

1. **`_analyze`** : comparez ce que gardent `standard` et `french` de la phrase « L'insuffisance cardiaque décompensée,
   pas de diabète ».
2. **Index `comptes_rendus_fr`** : analyseur `fr_medical` à l'indexation, le même avec les synonymes médicaux à la
   recherche. Rien à écrire.
3. **Tableau de comparaison** : expliquez chaque écart entre les deux index.

   | Requête | `comptes_rendus` | `comptes_rendus_fr` |
   |---|---|---|
   | diabète | 193 | 222 |
   | hta | 67 | 217 |
   | ic | 56 | 208 |
   | avc | 119 | 168 |
   | crise cardiaque | 311 | 120 |
   | infarctus du myocarde | 134 | 120 |

4. **Agrégations** (à écrire) : par service (`terms`), par trimestre (`date_histogram`), âge (`stats`), sur les
   222 comptes rendus qui mentionnent le diabète. Attendu : cardiologie 52, endocrinologie 44 ; âge moyen 57,1 ans.

## Partie 04 · Négation et cohorte (≈ 11 h 30)

1. Lisez les extraits en surbrillance : beaucoup disent « Aucun antécédent de diabète » ou « Père diabétique ».
2. Exécutez la cellule EDS-NLP : `diabète True False False`, puis `diabétique False True False`.
3. **Complétez la fonction `statut`** : familial si `e._.family`, hypothèse si `e._.hypothesis`, sinon affirmé.
   Attendu : 153 affirmés, 37 niés, 15 familiaux, 14 hypothèses, 3 sans mention reconnue.
4. Enrichissez l'index avec `diabete_statut` et filtrez : **153 comptes rendus, 112 patients**.

**À retenir** : chercher un mot ne suffit pas en clinique. Sur 222 comptes rendus trouvés par « diabète »,
69 ne décrivent pas un patient diabétique.

## Bonus : le mini moteur de recherche

`python interface/serveur.py`, puis http://localhost:8000 (README, section « Bonus »). Refaites-y les étapes du TP
sans écrire de JSON, et comparez avec vos chiffres : « insuffisance cardiaque » en *Mots* (344) puis en
*Expression exacte* (119), filtre Cardiologie à partir du 1er janvier 2026 (11), « diabete » en *Tolérant aux fautes*
(241). Ouvrez « La requête envoyée à OpenSearch » : c'est le JSON que vous avez écrit dans le notebook.
Avec l'index `comptes_rendus_fr` et le filtre « Diabète : affirmé », vous retrouvez la cohorte de la partie 04 (153).

## Pour aller plus loin

- Ajoutez au dictionnaire d'EDS-NLP les fautes de frappe de l'étape 4.
- Faites la même chose pour l'insuffisance cardiaque.
- Dans Dashboards (*Dev Tools*), retapez en JSON la requête de l'étape 3.
