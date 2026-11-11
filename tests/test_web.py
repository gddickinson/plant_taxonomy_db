"""Web interface tests: every exported endpoint answers, the static build is complete, and the JS engine tests pass.

Run: python -m pytest -q tests/test_web.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.app import STATIC, STATIC_ENDPOINTS, app  # noqa: E402

client = TestClient(app)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200 and "static/main.js" in r.text


@pytest.mark.parametrize("path", STATIC_ENDPOINTS)
def test_endpoint(path):
    r = client.get("/api" + path)
    assert r.status_code == 200, r.text
    assert r.json() is not None


def test_static_build(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static
    build_static.build(tmp_path / "site")
    assert (tmp_path / "site" / "index.html").read_text().count("APP_STATIC") == 1
    for path in STATIC_ENDPOINTS:
        assert (tmp_path / "site" / "api" / (path.strip("/") + ".json")).exists()


def test_static_assets_referenced_exist():
    html = (STATIC / "index.html").read_text()
    for name in ("style.css", "main.js"):
        assert f"static/{name}" in html and (STATIC / name).exists()


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_engine():
    tests = sorted(STATIC.glob("*.test.mjs"))
    for t in tests:
        r = subprocess.run(["node", str(t)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


# --- project-specific API tests (run on the committed ITIS subset; never call ITIS) ---------------------------------
from web import data  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "search_parity.json"


def _flatten(nodes):
    for n in nodes:
        yield n
        yield from _flatten(n["children"])


def test_web_does_not_load_network_clients():
    """The web app (and so the static build) never imports the ITIS/GBIF clients."""
    code = "import sys, web.app; print(any(m in sys.modules for m in ('api.itis_client', 'api.gbif_client', 'requests')))"
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == "False", r.stdout + r.stderr


def test_meta_describes_subset():
    m = client.get("/api/meta").json()
    assert m["subset"]["root_name"] and m["subset"]["downloaded"]
    assert m["focus"]["name"] == m["subset"]["root_name"]
    assert m["stats"]["total_taxa"] == len(client.get("/api/taxa").json())
    assert list(m["stats"]["by_rank"])[0] == "Kingdom"


def test_tree_holds_every_taxon_once():
    ids = [n["id"] for n in _flatten(client.get("/api/tree").json())]
    assert len(ids) == len(set(ids)) == len(data.index())


def test_taxon_detail_lineage_children_and_names():
    index = data.index()
    sp = next(t for t in index if t["rank"] == "Species" and t["common"])
    t = client.get(f"/api/taxon/{sp['id']}").json()
    assert t["lineage"][0]["rank"] == "Kingdom" and t["lineage"][-1]["rank"] == "Genus"
    assert t["name"].startswith(t["lineage"][-1]["name"] + " ")
    assert [c["name"] for c in t["common_names"]] == sp["common"]
    genus = client.get(f"/api/taxon/{t['lineage'][-1]['id']}").json()
    assert sp["id"] in [c["id"] for c in genus["children"]]
    assert genus["descendants"].get("Species", 0) >= 1
    assert any(client.get(f"/api/taxon/{x['id']}").json()["synonyms"] for x in index if x["rank"] == "Species")


def test_taxon_unknown_is_404():
    assert client.get("/api/taxon/999999999").status_code == 404


def test_search_rules():
    assert client.get("/api/search").json()["total"] == 0
    species = client.get("/api/search?rank=Species").json()
    assert species["total"] == data.meta()["stats"]["by_rank"]["Species"]
    pine = client.get("/api/search?q=pine").json()["results"]
    assert len({t["id"] for t in pine}) == len(pine) and any("pine" in " ".join(t["common"]).lower() for t in pine)


def test_search_fixture_is_current():
    """tests/fixtures/search_parity.json (used by search_engine.test.mjs) matches the Python search today."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import json

    import make_search_fixture
    assert json.loads(FIXTURE.read_text()) == json.loads(json.dumps(make_search_fixture.build(), ensure_ascii=False))


@pytest.mark.parametrize("name", ["test_plant_taxonomy.db", "myplants.db"])
def test_other_databases_browse(monkeypatch, name):
    """The local app can browse the other committed databases (ITIS-built and GBIF-built, the latter without TSNs)."""
    monkeypatch.setenv("PLANT_TAXONOMY_DB", str(ROOT / name))
    data.reset()
    try:
        m = client.get("/api/meta").json()
        assert m["subset"] is None and m["stats"]["total_taxa"] > 0
        tree = client.get("/api/tree").json()
        for n in list(_flatten(tree))[:30]:
            assert client.get(f"/api/taxon/{n['id']}").status_code == 200
        assert client.get("/api/search?q=a").json()["total"] > 0
    finally:
        monkeypatch.delenv("PLANT_TAXONOMY_DB")
        data.reset()
