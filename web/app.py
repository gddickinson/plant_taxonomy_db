"""FastAPI web app for Plant Taxonomy Database: serves the front end in static/ and the JSON API under /api.

Run with `python run_web.py` (http://127.0.0.1:8113, local only; `--db other.db` browses any database the repo built).
Data comes read-only from the database through web/data.py, which calls the repo's TaxonomyDatabase queries.
`scripts/build_static.py` exports every path in STATIC_ENDPOINTS to JSON for the GitHub Pages site, so keep that list
in step with the GET routes below. /api/search is answered on the static site by search_engine.js (same rules as
web/search.py) from the exported /api/taxa index.
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import data
from .search import search as run_search

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Plant Taxonomy Database")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/meta")
def meta():
    """Database name, statistics, the subset description, root taxa and the rank order."""
    return data.meta()


@app.get("/api/tree")
def tree():
    """The whole hierarchy as nested {id, name, rank, children}."""
    return data.tree()


@app.get("/api/taxa")
def taxa():
    """Every taxon as {id, tsn, name, rank, author, common}: the search index."""
    return data.index()


@app.get("/api/taxon/{taxon_id}")
def taxon(taxon_id: int):
    t = data.taxon(taxon_id)
    if t is None:
        raise HTTPException(404, f"no taxon with id {taxon_id}")
    return t


@app.get("/api/search")
def search(q: str = "", rank: str = ""):
    """Scientific or common name search (repo's search_by_name), optional rank filter."""
    return run_search(q, rank)


def _static_endpoints() -> list[str]:
    try:
        ids = [t["id"] for t in data.index()]
    except FileNotFoundError:
        ids = []
    return ["/meta", "/tree", "/taxa"] + [f"/taxon/{i}" for i in ids]


# GET paths (without the /api prefix) written to the static site as api/<path>.json.
STATIC_ENDPOINTS = _static_endpoints()
