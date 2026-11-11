"""Build a small taxonomy database of one ITIS subtree (default: the conifer order Pinales).

Uses the repo's own ITISClient and TaxonomyDatabase (via api/itis_subset.py). Needs internet access; the result is
committed (data/pinales_itis.db + .meta.json) so the web app, tests and the CI build never call ITIS.

Run: python scripts/build_itis_subset.py [--name Pinales] [--db data/pinales_itis.db] [--delay 0.2]
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.itis_client import ITISClient  # noqa: E402
from api.itis_subset import build_subtree, find_tsn  # noqa: E402
from database.db_manager import TaxonomyDatabase  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="Pinales", help="scientific name of the subtree root")
    ap.add_argument("--db", default=str(ROOT / "data" / "pinales_itis.db"))
    ap.add_argument("--delay", type=float, default=0.2, help="seconds between ITIS requests")
    ap.add_argument("--max", type=int, default=5000, help="safety cap on taxa")
    a = ap.parse_args()
    db_path = Path(a.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    client = ITISClient()
    tsn = find_tsn(client, a.name)
    with TaxonomyDatabase(str(db_path)) as db:
        db.create_schema()
        n = build_subtree(tsn, db, client, delay=a.delay, max_taxa=a.max,
                          progress=lambda i, t: print(f"{i:5d} {t.rank:12s} {t.scientific_name}", flush=True))
        stats = db.get_statistics()
        db.cursor.execute("SELECT COUNT(*) FROM synonyms")
        stats["total_synonyms"] = db.cursor.fetchone()[0]
    meta = {
        "root_name": a.name, "root_tsn": tsn, "subtree_taxa": n,
        "source": "ITIS (Integrated Taxonomic Information System), https://www.itis.gov",
        "service": ITISClient.BASE_URL, "downloaded": date.today().isoformat(),
        "builder": "scripts/build_itis_subset.py", "stats": stats,
    }
    db_path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
