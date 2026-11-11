# Session log

## 2026-11-11 -- web interface and GitHub Pages site (branch `web-interface`)

- Bugs found and fixed (separate commits, regression tests first):
  - `ITISClient.search_by_scientific_name` always returned `[]` (parsed `<scientificName>`, ITIS sends
    `<scientificNames>`), so every lookup silently fell back to GBIF.
  - `get_record` / `DataSourceManager.get_taxon_with_hierarchy` took the last entry of getFullHierarchyFromTSN as the
    requested taxon, but ITIS lists the taxon's children after it (Pinaceae came back as Tsuga; common names stored
    under the wrong TSN). New `ITISClient.split_lineage`.
  - `TaxonomyDatabase.search_by_name` listed a taxon twice when both its scientific and a common name matched.
- Added `api/itis_subset.py` + `scripts/build_itis_subset.py` (subtree download using ITISClient; authorship now kept
  from the hierarchy records) and built `data/pinales_itis.db` (order Pinales, ITIS, 2026-11-11).
- `models.taxonomy.RANK_ORDER`: added ITIS ranks it lacked (Infrakingdom, Superdivision, Infradivision, Superclass,
  Superorder, Subvariety, Subform); only used for ordering.
- Web interface `web/` (FastAPI, port 8113) + static site (`scripts/build_static.py`, `.github/workflows/pages.yml`):
  home, tree, taxon pages, search (JS mirror with parity fixture), ranks, about. README section, INTERFACE.md,
  THIRD_PARTY.md.
- `tests/test_offline.py` and `tests/test_comparative.py` were copies of the root scripts whose functions take
  arguments, so pytest reported 7 errors. Rewritten as real pytest tests (temp DB from utils/test_data.py; committed
  DBs); the root scripts stay as runnable walk-throughs. Whole `tests/` now collects with 0 errors.
- README roadmap: PyQt GUI for browsing marked done (taxonomy_gui.py, gui/).
- Not pushed; the lead reviews and merges.
