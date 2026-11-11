"""Write tests/fixtures/search_parity.json: the Python search (web/search.py) run on the committed database for a set
of queries, plus the search index, so web/static/search_engine.test.mjs can check the JS mirror gives the same ids.

Run after rebuilding the database: python scripts/make_search_fixture.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from models.taxonomy import RANK_ORDER  # noqa: E402
from web import data  # noqa: E402
from web.search import search  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "search_parity.json"
QUERIES = [
    ("pin", ""), ("Pinus", ""), ("pine", ""), ("PINE", ""), ("fir", ""), ("spruce", ""), ("cedar", ""), ("larch", ""),
    ("hemlock", ""), ("redwood", ""), ("yew", ""), ("cypress", ""), ("juniper", ""), ("a", ""), ("us", ""),
    ("var.", ""), ("ssp.", ""), ("p_n", ""), ("%ia", ""), ("Abies a", ""), ("  Picea  ", ""), ("é", ""), ("ü", ""),
    ("ñ", ""), ("zzz", ""), ("Cupressaceae", ""), ("aceae", ""), ("", ""), ("", "Species"), ("", "Genus"),
    ("", "Family"), ("", "Variety"), ("", "Subspecies"), ("pine", "Species"), ("a", "Variety"), ("x", "Genus"),
    ("Plantae", ""), ("tree", ""), ("Japanese", ""), ("mountain", "Species"), ("(", ""), (".", ""),
]


def build() -> dict:
    cases = []
    for q, rank in QUERIES:
        r = search(q, rank)
        cases.append({"q": q, "rank": rank, "total": r["total"], "ids": [t["id"] for t in r["results"]]})
    return {"database": data.db_path().name, "rank_order": RANK_ORDER, "index": data.index(), "cases": cases}


if __name__ == "__main__":
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(build(), ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"wrote {FIXTURE.relative_to(ROOT)}")
