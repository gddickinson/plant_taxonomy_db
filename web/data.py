"""Read-only access to a taxonomy database for the web app, through the repo's own TaxonomyDatabase queries.

The database defaults to the committed ITIS subset data/pinales_itis.db; set PLANT_TAXONOMY_DB (or run_web.py --db)
to browse any database built by the desktop app or populate_database.py. The file is opened read-only and every
query runs under one lock (FastAPI serves sync routes from a thread pool). Taxa are addressed by their row id, which
works for ITIS rows (with TSNs) and GBIF rows (without), as the repo's get_lineage_by_id / get_children_by_taxon_data do.
"""
import json
import os
import sqlite3
import sys
import threading
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from database.db_manager import TaxonomyDatabase  # noqa: E402
from models.taxonomy import RANK_ORDER, get_rank_level  # noqa: E402

DEFAULT_DB = ROOT / "data" / "pinales_itis.db"
_lock = threading.RLock()
_db = None


def db_path() -> Path:
    return Path(os.environ.get("PLANT_TAXONOMY_DB") or DEFAULT_DB)


def _open() -> TaxonomyDatabase:
    global _db
    if _db is None:
        path = db_path()
        if not path.exists():
            raise FileNotFoundError(f"taxonomy database not found: {path}")
        db = TaxonomyDatabase(str(path))
        # Same connection settings as TaxonomyDatabase.connect(), but read-only and usable from worker threads
        db.conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
        db.conn.row_factory = sqlite3.Row
        db.cursor = db.conn.cursor()
        _db = db
    return _db


def query(fn):
    """Run fn(db) under the lock."""
    with _lock:
        return fn(_open())


def summary(row: dict, common: list | None = None) -> dict:
    out = {"id": row["id"], "tsn": row.get("tsn"), "name": row["scientific_name"], "rank": row.get("rank"),
           "author": row.get("authorship")}
    if common is not None:
        out["common"] = common
    return out


def _sql(sql: str, args=()) -> list[dict]:
    def run(db):
        db.cursor.execute(sql, args)
        return [dict(r) for r in db.cursor.fetchall()]
    return query(run)


@lru_cache(maxsize=1)
def common_by_tsn() -> dict:
    """tsn -> [{name, language}] (duplicates removed, first-seen order)."""
    out: dict = {}
    for r in _sql("SELECT tsn, common_name, language FROM common_names ORDER BY id"):
        names = out.setdefault(r["tsn"], [])
        item = {"name": r["common_name"], "language": r["language"]}
        if item not in names:
            names.append(item)
    return out


@lru_cache(maxsize=1)
def all_rows() -> list[dict]:
    return _sql("SELECT * FROM taxa ORDER BY id")


@lru_cache(maxsize=1)
def index() -> list[dict]:
    """Every taxon as a summary with its common names: the search index (also used by the static site)."""
    cn = common_by_tsn()
    return [summary(r, [c["name"] for c in cn.get(r["tsn"], [])] if r["tsn"] is not None else []) for r in all_rows()]


def _row(taxon_id: int) -> dict | None:
    rows = _sql("SELECT * FROM taxa WHERE id = ?", (taxon_id,))
    return rows[0] if rows else None


def _roots() -> list[dict]:
    """Kingdoms, plus taxa with a TSN whose parent is not in the database."""
    tsns = {r["tsn"] for r in all_rows() if r["tsn"] is not None}
    return [r for r in all_rows() if r["rank"] == "Kingdom"
            or (r["tsn"] is not None and r["parent_tsn"] not in tsns)]


@lru_cache(maxsize=1)
def tree() -> list[dict]:
    """Nested {id, name, rank, children} built with the repo's get_children_by_taxon_data, from the roots down."""
    seen: set = set()

    def node(row: dict) -> dict:
        seen.add(row["id"])
        kids = query(lambda db: db.get_children_by_taxon_data(row))
        return {"id": row["id"], "name": row["scientific_name"], "rank": row["rank"],
                "children": [node(k) for k in kids if k["id"] not in seen]}
    return [node(r) for r in _roots() if r["id"] not in seen]


@lru_cache(maxsize=1)
def descendant_counts() -> dict:
    """id -> {rank: count} of all taxa below it in the tree."""
    out: dict = {}

    def walk(n: dict) -> dict:
        counts: dict = {}
        for c in n["children"]:
            counts[c["rank"]] = counts.get(c["rank"], 0) + 1
            for k, v in walk(c).items():
                counts[k] = counts.get(k, 0) + v
        out[n["id"]] = counts
        return counts
    for root in tree():
        walk(root)
    return out


def taxon(taxon_id: int) -> dict | None:
    """Detail record: the row, lineage (kingdom first), children, common names, synonyms, descendant counts."""
    row = _row(taxon_id)
    if row is None:
        return None
    lineage = query(lambda db: db.get_lineage_by_id(taxon_id))
    children = query(lambda db: db.get_children_by_taxon_data(row))
    tsn = row["tsn"]
    synonyms = _sql("SELECT synonym_tsn AS tsn, synonym_name AS name, synonym_author AS author FROM synonyms "
                    "WHERE accepted_tsn = ? ORDER BY synonym_name", (tsn,)) if tsn is not None else []
    accepted = _sql("SELECT t.id, t.scientific_name, t.rank FROM synonyms s JOIN taxa t ON t.tsn = s.accepted_tsn "
                    "WHERE s.synonym_tsn = ?", (tsn,)) if tsn is not None else []
    return {
        **{k: row[k] for k in row if k not in ("created_date", "updated_date")},
        "name": row["scientific_name"],
        "lineage": [summary(t) for t in lineage if t["id"] != taxon_id],
        "children": [summary(c) for c in children],
        "common_names": common_by_tsn().get(tsn, []) if tsn is not None else [],
        "synonyms": synonyms,
        "synonym_of": [summary({**a, "tsn": None, "authorship": None}) for a in accepted],
        "descendants": descendant_counts().get(taxon_id, {}),
    }


def meta() -> dict:
    """Database statistics (repo's get_statistics) plus the subset description written by build_itis_subset.py."""
    stats = query(lambda db: db.get_statistics())
    stats["total_synonyms"] = _sql("SELECT COUNT(*) AS n FROM synonyms")[0]["n"]
    stats["by_rank"] = dict(sorted(stats["by_rank"].items(), key=lambda kv: (get_rank_level(kv[0]), kv[0])))
    path = db_path()
    side = path.with_suffix(".meta.json")
    subset = json.loads(side.read_text()) if side.exists() else None
    roots = [summary(r) for r in _roots()]
    focus = next((r for r in all_rows() if subset and r["tsn"] == subset.get("root_tsn")), None)
    return {"database": path.name, "stats": stats, "subset": subset, "roots": roots,
            "focus": summary(focus) if focus else None, "rank_order": RANK_ORDER}


def reset():
    """Forget the open connection and cached results (after changing PLANT_TAXONOMY_DB)."""
    global _db
    with _lock:
        if _db is not None:
            _db.conn.close()
        _db = None
        for f in (common_by_tsn, all_rows, index, tree, descendant_counts):
            f.cache_clear()
