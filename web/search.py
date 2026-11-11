"""Taxon search for the web app: the repo's TaxonomyDatabase.search_by_name plus a rank filter, sorted and capped.

Mirrored by web/static/search_engine.js, which answers the same query on the static site from the exported index
(tests/test_web.py checks both give the same ids on many queries). Rules:
- `q` matches like SQL `LIKE '%q%'` (ASCII case-insensitive, `%` and `_` are wildcards) against the scientific name
  or any common name of the taxon (search_by_name).
- An empty `q` matches nothing unless `rank` is given, in which case every taxon of that rank matches.
- `rank`: keep only taxa of exactly that rank.
- Results are sorted by rank level (models.taxonomy.RANK_ORDER), then scientific name, then id, and capped at LIMIT.
"""
from models.taxonomy import get_rank_level

from . import data

LIMIT = 500


def search(q: str = "", rank: str = "") -> dict:
    q, rank = (q or "").strip(), (rank or "").strip()
    if not q and not rank:
        return {"q": q, "rank": rank, "total": 0, "results": []}
    rows = data.query(lambda db: db.search_by_name(q, limit=10 ** 9))
    if rank:
        rows = [r for r in rows if r["rank"] == rank]
    rows.sort(key=lambda r: (get_rank_level(r["rank"]), r["scientific_name"], r["id"]))
    by_id = {t["id"]: t for t in data.index()}
    return {"q": q, "rank": rank, "total": len(rows), "results": [by_id[r["id"]] for r in rows[:LIMIT]]}
