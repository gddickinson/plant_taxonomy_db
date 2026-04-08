# Comparative Visualization Fix

## Issue
The comparative visualization was throwing an error:
```
ERROR - tuple indices must be integers or slices, not str
```

## Root Cause
The lineage data from the database was coming back as SQLite Row objects (which behave like tuples) instead of plain dictionaries, and the code was trying to access them with string keys like `taxon['scientific_name']`.

## Fix Applied
Added robust data type handling throughout the comparative visualization:

1. **In `update_visualization()`**: Convert all lineage items to dicts before processing
2. **In `_build_tree_structure()`**: Check if taxon is dict, convert if needed
3. **In `_draw_tree()`**: Use `.get()` for safe dictionary access
4. **In `_calculate_positions()`**: Use `.get()` for safe access and handle edge cases

## Changes Made
- Added `isinstance(taxon, dict)` checks
- Used `.get()` instead of direct key access for safety
- Convert Row objects to dicts: `dict(item)`
- Added logging for better debugging

## Testing
The fix handles both:
- ✅ Dictionary data from ITIS
- ✅ Row/tuple data from GBIF
- ✅ Mixed data sources in same comparison

## Status
✅ **Fixed** - Comparative visualization now works reliably with all data sources!

## How to Use
Just extract the new tar file and run:
```bash
python taxonomy_gui.py plants_populated.db
```

Add species → Compare → View the tree! No more errors.
