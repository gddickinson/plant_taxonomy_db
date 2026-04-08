# Comparative Visualization Guide

## Overview

The **Compare Species** tab lets you visualize how multiple species are related by showing their common ancestors and divergence points in a phylogenetic-style tree.

## How to Use

### Step 1: Select Species to Compare

1. Browse or search for a species in the left panel
2. Click on a species (must be Species, Subspecies, or Variety rank)
3. Click the **"➕ Add to Comparison"** button below the search bar
4. Repeat for other species you want to compare

**Tip:** You can add species from different searches. Just search, add, search again, add, etc.

### Step 2: View the Comparison

1. Switch to the **"Compare Species"** tab
2. You'll see your selected species listed on the left
3. Click **"Compare Species"** button to generate the tree

### Step 3: Interpret the Tree

The comparative tree shows:
- **Nodes** - Each taxon in the hierarchy (color-coded by rank)
- **Connections** - Show evolutionary/taxonomic relationships
- **Common Ancestors** - Shared taxa where species diverged
- **Leaf Nodes** (squares) - Your selected species

**Color Key:**
- 🟢 Kingdom - Green
- 🔵 Division - Blue  
- 🟣 Class - Purple
- 🔴 Order - Red
- 🟠 Family - Orange
- 🔷 Genus - Turquoise
- 🟧 Species - Dark Orange (squares)

### Step 4: Export

Click **"Save Image"** to export as PNG, PDF, or SVG at 300 DPI.

## Example Workflows

### Example 1: Compare Species in Same Genus

**Goal:** See how different oak species are related

1. Search "Quercus alba" → Add to comparison
2. Search "Quercus robur" → Add to comparison  
3. Search "Quercus rubra" → Add to comparison
4. Switch to Compare Species tab
5. Click "Compare Species"

**Result:** Tree shows they share Kingdom → Division → Class → Order → Family → **Genus (Quercus)**, then diverge to different species.

### Example 2: Compare Species in Same Family

**Goal:** See relationships within Rosaceae family

1. Search "Rosa rugosa" → Add to comparison
2. Search "Malus domestica" (apple) → Add to comparison
3. Search "Prunus persica" (peach) → Add to comparison
4. Compare Species

**Result:** Tree shows they share up to **Family (Rosaceae)**, then diverge at genus level (Rosa, Malus, Prunus).

### Example 3: Compare Distant Species

**Goal:** See when evolutionary paths diverged

1. Add "Pinus ponderosa" (pine - gymnosperm)
2. Add "Quercus alba" (oak - angiosperm)
3. Add "Helianthus annuus" (sunflower - angiosperm)
4. Compare Species

**Result:** Pine diverges at Division level (Pinophyta vs Magnoliophyta), while oak and sunflower share more recent common ancestors.

## Features

### Managing Species List

- **Remove** - Select a species in the list, click "Remove"
- **Clear All** - Remove all species and start over
- **Add More** - Switch back to browser, find another species, add it

### Interactive Canvas

- **Zoom** - Use toolbar zoom buttons or scroll wheel
- **Pan** - Click and drag to move around
- **Reset** - Home button on toolbar resets view

### Understanding the Tree

**Branch Points** show where lineages diverged:
- High branch = distant relationship (diverged long ago)
- Low branch = close relationship (recent common ancestor)

**Example:**
```
         Kingdom
            |
        Division
         /     \
      Pine   Flowering
               /    \
            Rose   Oak
```

## Tips & Tricks

### Best Comparisons

**Good:**
- 2-5 species from same family
- Species from related genera
- Different species in same genus

**Less Useful:**
- Single species (nothing to compare)
- 10+ species (tree gets crowded)
- All from same species (no variation)

### Visual Clarity

For clearest results:
- Compare 2-4 species
- Choose species from different genera or families
- Save high-resolution images for presentations

### Performance

- Comparing 2-3 species: Instant
- Comparing 4-6 species: Very fast
- Comparing 7+ species: May take a moment to layout

## Troubleshooting

### "Not a Species" Error

**Problem:** Trying to add a Kingdom, Family, Genus, etc.

**Solution:** Only add Species-level taxa. Navigate down the tree until you see rank="Species"

### Empty Tree

**Problem:** Added species but tree shows "Select species to compare"

**Solution:** Click the "Compare Species" button to generate the tree

### Crowded Tree

**Problem:** Too many species, labels overlap

**Solution:**
1. Use toolbar zoom to focus on sections
2. Remove some species and re-compare
3. Export as large PNG and view in image viewer

### Species Not in Database

**Problem:** Want to compare species not yet added

**Solution:** 
1. Run `populate_database.py` with custom species list
2. Or add via enhanced demo: `python demo_enhanced.py --interactive`

## Scientific Use Cases

### Research

- **Phylogenetic studies** - Visualize evolutionary relationships
- **Taxonomy validation** - Verify classification is consistent
- **Literature figures** - Export high-quality images for papers

### Teaching

- **Evolution concepts** - Show divergence and common ancestry
- **Plant families** - Demonstrate family characteristics
- **Classification systems** - Explain hierarchical taxonomy

### Data Exploration

- **Database validation** - Check if relationships make sense
- **Coverage analysis** - See which clades are well-represented
- **Gap identification** - Find missing taxonomic groups

## Advanced: Interpreting Branch Patterns

### Polytomy (Multiple Branches)

When 3+ species branch from same point:
- May indicate rapid diversification
- Could mean database lacks intermediate taxa
- Common in cultivated varieties

### Long Branches

Long vertical lines indicate:
- Many taxonomic ranks between species
- Potential missing data in database
- Ancient lineages

### Symmetry

Balanced trees suggest:
- Comprehensive sampling
- Natural radiation patterns
- Good database coverage

Unbalanced trees suggest:
- Biased sampling
- Recent diversification in one clade
- Missing data

## Export Options

### PNG (Raster)
- Best for: Presentations, web
- Resolution: 300 DPI
- File size: Medium

### PDF (Vector)
- Best for: Publications, printing
- Resolution: Scalable
- File size: Small

### SVG (Vector)
- Best for: Further editing in Illustrator/Inkscape
- Resolution: Infinite
- File size: Small

## Future Enhancements

Potential additions:
- [ ] Distance metrics on branches
- [ ] Time calibration (if age data available)
- [ ] Support for comparing genera/families
- [ ] Export to Newick format
- [ ] Color by trait/characteristic
- [ ] Interactive node labels (hover for details)

---

**Happy comparing!** 🌿

This feature helps you see the "big picture" of how species are related, making taxonomy more intuitive and visual.
