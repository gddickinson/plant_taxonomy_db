# Plant Taxonomy Database -- Roadmap

## Current State
A functional plant taxonomy database application with SQLite storage, ITIS API integration, and a GBIF client. Has a well-organized modular structure: `database/db_manager.py`, `api/itis_client.py`, `api/gbif_client.py`, `api/data_source_manager.py`, `models/taxonomy.py`, `utils/formatting.py`. Includes a PyQt GUI (`taxonomy_gui.py`), comparative visualization (`gui/comparative_viz.py`), a demo script, and test files (`test_offline.py`, `test_comparative.py`). The `db_manager.py` uses context managers and type hints well. Has a `populate_database.py` for bulk loading and `launcher.py` for startup.

## Short-term Improvements
- [ ] Add proper error handling in `itis_client.py` for network timeouts and API rate limits (already has retry + exponential backoff)
- [ ] Add retry logic with exponential backoff in `api/data_source_manager.py` (already delegates to clients which have it)
- [x] Move `test_offline.py` and `test_comparative.py` into a `tests/` directory and use pytest
- [ ] Add input sanitization in `db_manager.py` for SQL injection prevention (parameterized queries check)
- [x] Add `requirements.txt` with version pins (currently only `requests` mentioned)
- [x] Create `INTERFACE.md` for project navigation
- [ ] Add logging to `itis_client.py` and `gbif_client.py` instead of print statements (already uses logging)

## Feature Enhancements
- [ ] Implement batch download in `api/data_source_manager.py` -- bulk-fetch entire plant families
- [ ] Add CSV/JSON export functionality in `utils/formatting.py`
- [ ] Implement USDA PLANTS Database client (`api/usda_client.py`) as listed in Phase 2
- [ ] Add taxonomic tree visualization in `gui/visualization.py` using matplotlib or pyqtgraph
- [ ] Implement full-text search across scientific names, common names, and synonyms
- [ ] Add geographic distribution data integration (GBIF occurrence records)
- [ ] Add a CLI tool with argparse for headless database operations

## Long-term Vision
- [ ] Add image integration -- fetch plant photos from Wikimedia Commons or iNaturalist
- [ ] Implement genome database links (NCBI, Phytozome, Ensembl Plants)
- [ ] Build a web interface with Flask/FastAPI for browser-based browsing
- [ ] Add World Flora Online integration for global species coverage
- [ ] Implement database synchronization for multi-user access
- [ ] Package as a standalone desktop app with PyInstaller

## Technical Debt
- [x] `taxonomy_gui.py` is likely a large monolithic file -- split into separate widget modules
- [ ] `demo.py` and `demo_enhanced.py` overlap -- consolidate into one demo with flags
- [ ] `utils/test_data.py` should be in `tests/` not `utils/`
- [ ] Add type hints to `gui/visualization.py` and `gui/comparative_viz.py`
- [ ] Add database migration support for schema changes (alembic or manual versioning)
- [ ] `launcher.py` should handle missing dependencies gracefully with user-friendly messages
