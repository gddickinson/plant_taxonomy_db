# Third-party data

## ITIS (Integrated Taxonomic Information System)

`data/pinales_itis.db` (with `data/pinales_itis.meta.json`) and the recorded responses in `tests/fixtures/itis/` were
downloaded from the ITIS web services (https://www.itis.gov/ITISWebService/services/ITISService) on **2026-11-11**
by `scripts/build_itis_subset.py` (the repo's own `ITISClient` and `TaxonomyDatabase`).

Contents: the order Pinales (conifers, ITIS TSN 500028) and every taxon below it, with its lineage up to the kingdom
Plantae, common names and synonyms. It is a subset for the web site and tests, not all plants. ITIS is updated
continually; rebuild with `python scripts/build_itis_subset.py` (needs internet) for current data.

Licence: ITIS data are produced by the US government and are in the public domain (CC0); ITIS asks for this citation:

> Retrieved November 11, 2026, from the Integrated Taxonomic Information System (ITIS) on-line database,
> www.itis.gov, CC0 https://doi.org/10.5066/F7KH0KBK

The other committed databases (`test_plant_taxonomy.db`, `myplants.db`, `demo_plant_taxonomy.db`) predate this file;
`myplants.db` was built through the GBIF fallback (see `api/gbif_client.py`).
