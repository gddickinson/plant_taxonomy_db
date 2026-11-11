# Plant Taxonomy Database -- Interface Map

## Project Overview
A plant taxonomy database application with SQLite storage, ITIS/GBIF API
integration, a PyQt5 GUI, and comparative visualization tools.

## Core Modules

### `database/`
- **`db_manager.py`** -- SQLite database manager
  - `TaxonomyDatabase` -- CRUD operations, search, lineage traversal, statistics
  - Context manager support (`with TaxonomyDatabase(...) as db:`)

### `api/`
- **`itis_client.py`** -- ITIS web services client
  - `ITISClient` -- search, hierarchy, common names; has retry + exponential backoff
  - `ITISClient.split_lineage(hierarchy, tsn)` -- (lineage, taxon) from a getFullHierarchyFromTSN result
    (ITIS lists the taxon's children after it)
  - Custom exceptions: `ITISError`, `ITISConnectionError`, `ITISDataError`
- **`gbif_client.py`** -- GBIF REST API client
  - `GBIFClient` -- species search, classification, occurrence records
- **`data_source_manager.py`** -- Multi-source manager with fallback
  - `DataSourceManager` -- tries ITIS then GBIF (or vice versa)
- **`itis_subset.py`** -- Download one ITIS subtree into a TaxonomyDatabase
  - `build_subtree()`, `find_tsn()`, `get_synonyms()`, `get_common_names_detailed()`, `with_classification()`

### `models/`
- **`taxonomy.py`** -- Taxon data model
  - `Taxon` dataclass with hierarchical fields and serialization

### `gui/`
- **`browser_widget.py`** -- Extracted widget classes
  - `TaxonomyBrowserWidget` -- tree-based hierarchy browser with search
  - `TaxonDetailsWidget` -- HTML-formatted taxon detail view
  - `StatisticsWidget` -- database statistics display
- **`visualization.py`** -- Lineage visualization widget (matplotlib)
  - `TaxonomyVisualizationWidget`
- **`comparative_viz.py`** -- Side-by-side species comparison widget
  - `ComparativeVisualizationWidget`

### Root
- **`taxonomy_gui.py`** -- Main PyQt5 window (imports widgets from gui/)
  - `PlantTaxonomyGUI` -- main window with menus, toolbar, tabbed layout

### `utils/`
- **`formatting.py`** -- Display formatting utilities
  - `print_taxon_info()`, `format_lineage()`, `get_taxon_summary()`
- **`logger.py`** -- Logging configuration
  - `get_logger()`, `setup_quick_logging()`

### `web/` -- web interface (FastAPI + plain ES modules, no build step)
- **`app.py`** -- routes under /api (`meta`, `tree`, `taxa`, `taxon/{id}`, `search`), `STATIC_ENDPOINTS` for the export
- **`data.py`** -- read-only DB access via `TaxonomyDatabase` (`tree()`, `taxon()`, `index()`, `meta()`, `reset()`);
  DB = `PLANT_TAXONOMY_DB` or `data/pinales_itis.db`
- **`search.py`** -- `search(q, rank)`: `search_by_name` + rank filter, sorted, capped (mirrored in JS)
- **`static/`** -- `index.html`, `core.js` (router, api), `main.js`, pages `home.js` (home/ranks/about), `tree.js`,
  `taxon.js`, `search.js`; `ui.js` helpers; `search_engine.js` (+ `.test.mjs`) and `static_api.js` for the static site;
  `style.css` (shared kit theme), `style_app.css`

### `scripts/`
- **`build_itis_subset.py`** -- build `data/pinales_itis.db` + `.meta.json` from ITIS (needs internet)
- **`make_search_fixture.py`** -- write `tests/fixtures/search_parity.json` (Python search results for the JS test)
- **`build_static.py`** -- export the static GitHub Pages site to `site/`
- **`screenshots.py`** -- Playwright smoke test of routes + README screenshots (`docs/img/`)

### `data/`
- **`pinales_itis.db`** -- ITIS subset (order Pinales, downloaded 2026-11-11; see THIRD_PARTY.md)

## Entry Points
- **`launcher.py`** -- Application launcher (dependency checks)
- **`demo.py`** -- Interactive demo with ITIS API
- **`demo_enhanced.py`** -- Enhanced demo with GBIF support
- **`populate_database.py`** -- Bulk database population script
- **`run_web.py`** -- web app on http://127.0.0.1:8113 (`--db` for another database)

## Tests: `tests/`
- **`test_db_manager.py`** -- Database CRUD smoke tests
- **`test_offline.py`** -- Offline test suite (moved from root)
- **`test_comparative.py`** -- Comparative viz data handling (moved from root)
- **`test_itis_client.py`** -- ITISClient parsing on recorded ITIS XML (`fixtures/itis/`), no network
- **`test_itis_subset.py`** -- subtree builder helpers on recorded XML
- **`test_web.py`** -- web API, static build, JS tests (node), search parity fixture is current

## Test Data
- **`utils/test_data.py`** -- Sample taxonomic data for offline testing
  - `get_all_test_taxa()`, `get_test_taxon()`

## Archived: `_archive/`
- `demo_enhanced.py` -- consolidated into demo.py (if applicable)
