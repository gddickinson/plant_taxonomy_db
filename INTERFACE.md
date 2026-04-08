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
  - Custom exceptions: `ITISError`, `ITISConnectionError`, `ITISDataError`
- **`gbif_client.py`** -- GBIF REST API client
  - `GBIFClient` -- species search, classification, occurrence records
- **`data_source_manager.py`** -- Multi-source manager with fallback
  - `DataSourceManager` -- tries ITIS then GBIF (or vice versa)

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

## Entry Points
- **`launcher.py`** -- Application launcher (dependency checks)
- **`demo.py`** -- Interactive demo with ITIS API
- **`demo_enhanced.py`** -- Enhanced demo with GBIF support
- **`populate_database.py`** -- Bulk database population script

## Tests: `tests/`
- **`test_db_manager.py`** -- Database CRUD smoke tests
- **`test_offline.py`** -- Offline test suite (moved from root)
- **`test_comparative.py`** -- Comparative viz data handling (moved from root)

## Test Data
- **`utils/test_data.py`** -- Sample taxonomic data for offline testing
  - `get_all_test_taxa()`, `get_test_taxon()`

## Archived: `_archive/`
- `demo_enhanced.py` -- consolidated into demo.py (if applicable)
