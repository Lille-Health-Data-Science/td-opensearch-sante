# TD OpenSearch · M2 Data Science en santé

Séance 3 de l'option Data (Université de Lille) : **samedi 21 novembre 2026, 8 h – 12 h**.
Ce dossier installe **OpenSearch 3.8.0** et son interface **Dashboards**, et contient le corpus et le notebook
de la séance. Le déroulé pas à pas est dans **[TD.md](TD.md)**, les slides du cours dans
**[supports/03-opensearch.pdf](supports/03-opensearch.pdf)**.

> Le corpus `donnees/comptes_rendus.ndjson` est **entièrement fictif** : 600 comptes rendus, aucun patient réel.
> La sécurité d'OpenSearch est désactivée pour le TP : jamais de données réelles dans cette installation.

L'installation se fait **en début de séance**, pendant l'introduction. Les images à télécharger pèsent environ
1,5 Go : avec 30 personnes sur le même Wi-Fi, lancez-la dès 8 h.

| Votre situation | Voie | À télécharger sur votre ordinateur |
|---|---|---|
| Docker Desktop déjà installé, 8 Go de mémoire ou plus | A · Docker | environ 1,5 Go (images) + 300 Mo (Python) |
| Pas de Docker, ou moins de 8 Go de mémoire | B · Codespaces | rien (tout se passe chez GitHub) |

## Ce qu'il faut

- Un compte GitHub (voie B) ou Docker Desktop (voie A), et Python 3.10 ou plus (voie A).
- Ce dossier :
  ```bash
  git clone https://github.com/Lille-Health-Data-Science/td-opensearch-sante.git
  cd td-opensearch-sante
  ```

## A · Docker

```bash
docker compose up -d                       # OpenSearch (port 9200) et Dashboards (port 5601)
python -m venv .venv
source .venv/bin/activate                  # Windows : .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook seance3_etudiant.ipynb
```

OpenSearch met environ une minute à démarrer. Dashboards : http://localhost:5601 (pas de mot de passe).

Si votre ordinateur manque de mémoire, lancez seulement le moteur : `docker compose up -d opensearch`.
Tout le notebook fonctionne sans Dashboards.

## B · Codespaces (dans le navigateur)

1. Sur la page GitHub du dépôt : *Code › Codespaces › Create codespace on main*.
2. **Si l'éditeur demande « Faites-vous confiance aux auteurs des fichiers de ce dossier ? », cliquez sur
   « Approuver le dossier et continuer »** : en mode restreint, rien ne démarre.
3. L'installation se fait seule (3 à 5 min) : les paquets Python, puis OpenSearch et Dashboards.
4. Ouvrez `seance3_etudiant.ipynb` et choisissez le noyau Python proposé.

Dashboards : onglet **Ports** en bas de l'éditeur, ligne **5601**, icône globe.
Si OpenSearch n'a pas démarré, ouvrez un terminal (*Terminal › New Terminal*) et tapez `docker compose up -d`.

## Vérifier que tout marche

1. `curl localhost:9200` répond avec `"number" : "3.8.0"` (dans un terminal).
2. La première cellule du notebook affiche « OpenSearch 3.8.0 répond sur localhost ».
3. Dashboards s'ouvre ; dans *Dev Tools*, `GET _cluster/health` répond `"status" : "green"` ou `"yellow"`.

## Bonus : un mini moteur de recherche

Une page de recherche toute prête sur le corpus : champ de recherche, choix entre mots, expression exacte et
recherche tolérante aux fautes, filtres par service et par date, extraits surlignés, comptes par service, et la
requête JSON envoyée à OpenSearch, à recopier dans *Dev Tools*. Rien à installer en plus.

```bash
python interface/serveur.py
```

Puis ouvrez http://localhost:8000 (Codespaces : onglet **Ports**, ligne **8000**). Si l'index `comptes_rendus`
n'existe pas encore, la page propose de l'indexer. L'index `comptes_rendus_fr` et le filtre « Diabète » apparaissent
quand vous avez fait les parties 03 et 04 du notebook. Ctrl+C dans le terminal pour arrêter.

## En cas de problème

| Symptôme | Solution |
|---|---|
| `ConnectionError` dans le notebook | OpenSearch démarre encore : attendre une minute, puis relancer la cellule. Sinon `docker compose ps` et `docker compose logs opensearch` |
| Le conteneur `opensearch` s'arrête au démarrage (Linux) | `sudo sysctl -w vm.max_map_count=262144`, puis `docker compose up -d` |
| `unknown shorthand flag: 'd' in -d` | Docker sans le module Compose (Mac avec Homebrew et Colima) : `brew install docker-compose`, puis `mkdir -p ~/.docker/cli-plugins && ln -sfn "$(brew --prefix)/opt/docker-compose/bin/docker-compose" ~/.docker/cli-plugins/docker-compose`. Ou taper `docker-compose up -d` |
| `Cannot connect to the Docker daemon` | Lancer Docker Desktop, attendre qu'il soit prêt |
| `port is already allocated` (9200 ou 5601) | Un autre OpenSearch tourne : `docker compose down` dans l'autre dossier, ou fermer l'autre conteneur |
| Téléchargement trop lent sur le Wi-Fi | Passer en voie B (Codespaces) |
| Codespaces : « running in recovery mode due to a configuration error » | Codespace créé avant le correctif du 21 novembre : supprimer le codespace et en créer un nouveau (ou `git pull`, puis *Codespaces: Rebuild Container*) |
| Codespaces : rien ne démarre | Approuver le dossier (bannière « mode Restreint » en haut), puis `docker compose up -d` dans un terminal |
| `ModuleNotFoundError` | `pip install -r requirements.txt` dans l'environnement du notebook |
| Autre chose | Montrer le message à l'enseignant |

## Contenu du dossier

| Élément | Rôle |
|---|---|
| `TD.md` | Déroulé de la séance, avec ce qu'on doit voir à chaque étape |
| `supports/03-opensearch.pdf` | Les slides du cours (71 slides) |
| `seance3_etudiant.ipynb` | Le notebook : index inversé en Python (partie 01), TP requêtes (partie 02), analyse et agrégations (partie 03), négation avec EDS-NLP (partie 04) |
| `donnees/comptes_rendus.ndjson` | 600 comptes rendus fictifs (identifiant, patient, titre, service, date, âge, sexe, texte) |
| `docker-compose.yml` | OpenSearch 3.8.0 et Dashboards 3.8.0, un seul nœud, sécurité désactivée |
| `interface/` | Bonus : mini moteur de recherche (`serveur.py` et `index.html`, bibliothèque standard de Python seulement) |
| `requirements.txt` | opensearch-py, pandas, matplotlib, EDS-NLP, Jupyter |
| `.devcontainer/` | Configuration GitHub Codespaces (voie B) |

La séance 4 assemble les trois briques : FHIR (séance 1), Airflow (séance 2) et OpenSearch.
