"""Mini moteur de recherche pour le corpus de la séance 3 (bonus).

Lance un petit serveur web qui sert une page de recherche et transmet les requêtes à OpenSearch.
Aucun paquet à installer : seulement la bibliothèque standard de Python.

    python interface/serveur.py            puis ouvrir http://localhost:8000

Variables facultatives : OPENSEARCH_URL (défaut http://localhost:9200), PORT (défaut 8000).
"""
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

OPENSEARCH = os.environ.get("OPENSEARCH_URL", "http://localhost:9200").rstrip("/")
PORT = int(os.environ.get("PORT", "8000"))
ICI = Path(__file__).resolve().parent
CORPUS = ICI.parent / "donnees" / "comptes_rendus.ndjson"
INDEX_AUTORISES = {"comptes_rendus", "comptes_rendus_fr"}
PAR_PAGE = 10

MAPPING = {"mappings": {"properties": {
    "titre": {"type": "text", "analyzer": "french"},
    "contenu": {"type": "text", "analyzer": "french"},
    "service": {"type": "keyword"}, "date_creation": {"type": "date"}, "age": {"type": "integer"},
    "sexe": {"type": "keyword"}, "patient_id": {"type": "keyword"},
}}}


def appel(methode, chemin, corps=None, ndjson=False):
    """Envoie une requête à OpenSearch et renvoie (code HTTP, réponse JSON)."""
    data = None
    entetes = {}
    if corps is not None:
        data = corps.encode() if ndjson else json.dumps(corps).encode()
        entetes["Content-Type"] = "application/x-ndjson" if ndjson else "application/json"
    req = urllib.request.Request(OPENSEARCH + chemin, data=data, method=methode, headers=entetes)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def construire_requete(p):
    """Traduit les champs du formulaire en requête OpenSearch (Query DSL)."""
    texte = p.get("q", "").strip()
    mode = p.get("mode", "match")
    must, filtres = [], []
    if texte:
        if mode == "phrase":
            must.append({"match_phrase": {"contenu": texte}})
        elif mode == "flou":
            must.append({"match": {"contenu": {"query": texte, "fuzziness": "AUTO"}}})
        else:
            must.append({"match": {"contenu": texte}})
    if p.get("service"):
        filtres.append({"term": {"service": p["service"]}})
    plage = {k: v for k, v in (("gte", p.get("du")), ("lte", p.get("au"))) if v}
    if plage:
        filtres.append({"range": {"date_creation": plage}})
    if p.get("statut"):
        filtres.append({"term": {"diabete_statut": p["statut"]}})
    requete = {"query": {"bool": {"must": must or [{"match_all": {}}], "filter": filtres}}}
    if p.get("tri") == "date":
        requete["sort"] = [{"date_creation": "desc"}]
    page = max(int(p.get("page", "1") or 1), 1)
    requete.update({
        "from": (page - 1) * PAR_PAGE, "size": PAR_PAGE,
        "_source": ["titre", "service", "date_creation", "age", "sexe", "patient_id"],
        "highlight": {"encoder": "html", "pre_tags": ["<mark>"], "post_tags": ["</mark>"],
                      "fields": {"contenu": {"fragment_size": 160, "number_of_fragments": 2}}},
        "aggs": {"par_service": {"terms": {"field": "service", "size": 20}}},
    })
    return requete


def rechercher(p):
    index = p.get("index", "comptes_rendus")
    if index not in INDEX_AUTORISES:
        return 400, {"erreur": "Index inconnu."}
    requete = construire_requete(p)
    code, rep = appel("POST", f"/{index}/_search", requete)
    if code == 404:
        return 404, {"erreur": f"L'index {index} n'existe pas encore.", "requete": requete}
    if code != 200:
        raison = rep.get("error", {}).get("root_cause", [{}])[0].get("reason", str(rep)[:300])
        return code, {"erreur": f"OpenSearch a refusé la requête : {raison}", "requete": requete}
    resultats = []
    for h in rep["hits"]["hits"]:
        s = h["_source"]
        resultats.append({
            "id": h["_id"], "score": h["_score"], "titre": s.get("titre"), "service": s.get("service"),
            "date": s.get("date_creation"), "age": s.get("age"), "sexe": s.get("sexe"),
            "patient": s.get("patient_id"),
            "extraits": h.get("highlight", {}).get("contenu", []),
        })
    return 200, {
        "total": rep["hits"]["total"]["value"], "duree_ms": rep.get("took"),
        "resultats": resultats, "par_page": PAR_PAGE,
        "par_service": [{"cle": b["key"], "nombre": b["doc_count"]}
                        for b in rep["aggregations"]["par_service"]["buckets"]],
        "requete": requete,
    }


def etat():
    """Version d'OpenSearch, index présents et nombre de documents."""
    try:
        _, info = appel("GET", "/")
    except OSError:
        return 503, {"erreur": f"OpenSearch ne répond pas sur {OPENSEARCH}. Est-il lancé ?"}
    index = {}
    for nom in sorted(INDEX_AUTORISES):
        code, rep = appel("GET", f"/{nom}/_count")
        if code == 200:
            index[nom] = rep["count"]
    _, statut = appel("GET", "/comptes_rendus_fr/_mapping")
    a_statut = "diabete_statut" in json.dumps(statut)
    return 200, {"version": info.get("version", {}).get("number"), "index": index, "statut_diabete": a_statut}


def indexer():
    """Crée l'index comptes_rendus (analyseur french) et y charge le corpus, s'il n'existe pas ou s'il est vide."""
    code, rep = appel("GET", "/comptes_rendus/_count")
    if code == 200 and rep.get("count"):
        return 200, {"message": "L'index comptes_rendus existe déjà et n'est pas vide."}
    if code == 200:
        appel("DELETE", "/comptes_rendus")         # index créé mais resté vide : on le recrée
    appel("PUT", "/comptes_rendus", MAPPING)
    lignes = []
    for ligne in CORPUS.read_text(encoding="utf-8").splitlines():
        doc = json.loads(ligne)
        lignes.append(json.dumps({"index": {"_index": "comptes_rendus", "_id": doc["id"]}}))
        lignes.append(json.dumps(doc, ensure_ascii=False))
    code, rep = appel("POST", "/_bulk?refresh=true", "\n".join(lignes) + "\n", ndjson=True)
    if code != 200 or rep.get("errors"):
        return 500, {"erreur": "Le chargement a échoué."}
    return 200, {"message": f"{len(lignes) // 2} comptes rendus indexés dans comptes_rendus."}


class Gestionnaire(BaseHTTPRequestHandler):
    def envoyer(self, code, corps, type_="application/json; charset=utf-8"):
        data = corps if isinstance(corps, bytes) else json.dumps(corps, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", type_)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        p = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path in ("/", "/index.html"):
                self.envoyer(200, (ICI / "index.html").read_bytes(), "text/html; charset=utf-8")
            elif url.path == "/api/recherche":
                self.envoyer(*rechercher(p))
            elif url.path == "/api/etat":
                self.envoyer(*etat())
            else:
                self.envoyer(404, {"erreur": "Page introuvable."})
        except OSError:
            self.envoyer(503, {"erreur": f"OpenSearch ne répond pas sur {OPENSEARCH}. Est-il lancé ?"})

    def do_POST(self):
        if urlparse(self.path).path == "/api/indexer":
            try:
                self.envoyer(*indexer())
            except OSError:
                self.envoyer(503, {"erreur": f"OpenSearch ne répond pas sur {OPENSEARCH}."})
        else:
            self.envoyer(404, {"erreur": "Page introuvable."})

    def log_message(self, *args):
        pass  # pas de journal à chaque requête


if __name__ == "__main__":
    print(f"Mini moteur de recherche : http://localhost:{PORT}  (OpenSearch : {OPENSEARCH})")
    print("Ctrl+C pour arrêter.")
    ThreadingHTTPServer(("0.0.0.0", PORT), Gestionnaire).serve_forever()
