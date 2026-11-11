"""Web interface for the Plant Taxonomy Database (FastAPI + plain ES-module front end).

- app.py: FastAPI app, JSON API under /api, STATIC_ENDPOINTS for the GitHub Pages export
- data.py: read-only database access through the repo's TaxonomyDatabase (tree, taxon detail, index, statistics)
- search.py: search rules (repo's search_by_name + rank filter), mirrored by static/search_engine.js
- static/: the front end (index.html, core.js router, one module per page)
"""
