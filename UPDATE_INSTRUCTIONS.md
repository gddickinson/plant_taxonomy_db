# How to Update to Fix Comparative Visualization

## The Issue

You're getting this error:
```
ERROR - tuple indices must be integers or slices, not str
```

This happens because you're running an older version of the code that doesn't handle database rows properly.

## Solution: Update to Latest Version

### Step 1: Download New Version

Download the latest `plant_taxonomy_db_enhanced.tar.gz` file.

### Step 2: Extract in New Location

**IMPORTANT:** Extract to a NEW directory or remove the old one first!

```bash
# Option A: Remove old directory first
rm -rf plant_taxonomy_db
tar -xzf plant_taxonomy_db_enhanced.tar.gz
cd plant_taxonomy_db_enhanced

# Option B: Extract to different name
tar -xzf plant_taxonomy_db_enhanced.tar.gz
mv plant_taxonomy_db_enhanced plant_taxonomy_new
cd plant_taxonomy_new
```

### Step 3: Test the Fix

Run this test to verify it's working:

```bash
python test_comparative.py plants_populated.db
```

Expected output:
```
COMPARATIVE VISUALIZATION TEST
Loading database: plants_populated.db
Searching for species...
Found 10 species

Testing lineage retrieval...
[1] Rosa rugosa
  Lineage has 3 ranks
  ✓ Lineage data format OK
  Kingdom → Family → Species

✓ ALL TESTS PASSED
Comparative visualization should work!
```

### Step 4: Launch GUI

```bash
python taxonomy_gui.py plants_populated.db
```

### Step 5: Try Comparative Visualization

1. Browse to a species (e.g., Rosa rugosa)
2. Click "➕ Add to Comparison"
3. Browse to another species (e.g., Quercus alba)
4. Click "➕ Add to Comparison"
5. Switch to "Compare Species" tab
6. Click "Compare Species" button

**Should work with no errors!** ✅

## If You Still Get Errors

### Check Your Version

Make sure you're in the RIGHT directory:

```bash
# Check if the file has the fix
grep -n "isinstance(item, dict)" gui/comparative_viz.py
```

Should show line numbers like: `389:if isinstance(item, dict):`

If you don't see this, you're in the old directory!

### Close and Restart

If the GUI is still running from before:
1. Close the GUI completely
2. Make sure you're in the NEW directory
3. Launch again: `python taxonomy_gui.py plants_populated.db`

### Python Cache

Sometimes Python caches old code:

```bash
# Remove cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Or just restart Python/terminal
```

## What Was Fixed

The code now properly converts SQLite Row objects to dictionaries before processing:

```python
# NEW CODE (fixed):
for item in lineage:
    if isinstance(item, dict):
        lineage_dicts.append(item)
    else:
        lineage_dicts.append(dict(item))  # Convert Row to dict
```

This ensures the code can access fields like `taxon['scientific_name']` without errors.

## Quick Verification

Run the test script to verify everything is working:

```bash
python test_comparative.py plants_populated.db
```

If this passes, the GUI will work too!

---

**After updating, comparative visualization should work perfectly!** 🌿
