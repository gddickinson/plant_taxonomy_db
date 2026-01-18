# Plant Taxonomy Database - GUI Guide

## Overview

The Plant Taxonomy Database now includes a full-featured PyQt5 GUI for browsing, searching, and visualizing taxonomic data.

## Features

### 🌳 Hierarchical Browser
- Navigate taxonomy tree from Kingdom to Species
- Lazy loading for efficient browsing
- Visual tree structure with expand/collapse

### 🔍 Search Functionality
- Search by scientific names
- Search by common names  
- Real-time results display
- Click any result to see full details

### 📊 Detailed Views
- Complete taxonomic lineage
- Common names
- Authority/authorship information
- Child taxa listing
- Source information (ITIS/GBIF)

### 📈 Statistics Dashboard
- Total taxa count
- Common names count
- Taxa breakdown by rank
- Real-time refresh

### 🎨 Visualization
- Linear lineage visualization
- Color-coded by taxonomic rank
- Save visualizations as PNG/PDF/SVG
- Interactive matplotlib canvas

## Installation

### Prerequisites

```bash
pip install -r requirements.txt
```

This installs:
- `requests` - API communication
- `PyQt5` - GUI framework
- `matplotlib` - Visualization

### Quick Start

**Step 1: Populate Database**
```bash
# Populate with diverse plant species (takes 5-10 minutes)
python populate_database.py --db plants.db

# Or add fewer species for quick testing
python populate_database.py --db test.db --max 10
```

**Step 2: Launch GUI**
```bash
# Launch GUI
python taxonomy_gui.py

# Or auto-load a database
python taxonomy_gui.py plants.db
```

## GUI Walkthrough

### Main Window Layout

```
┌─────────────────────────────────────────────────────┐
│ File   Help                                    [×]  │
├─────────────────────────────────────────────────────┤
│ [Open Database] | [Refresh]                        │
├──────────────────┬──────────────────────────────────┤
│                  │ ┌─────────────────────────────┐ │
│  Search: [____]  │ │ Details│Stats│Visualization│ │
│                  │ ├─────────────────────────────┤ │
│  ┌─┐ Plantae     │ │                            │ │
│  │-│  Kingdom    │ │   Taxon Details View       │ │
│  └┬┐             │ │                            │ │
│   ├─ Tracheo...  │ │   - Full Lineage          │ │
│   ├─ Magnoli...  │ │   - Common Names          │ │
│   └─ ...         │ │   - Children List         │ │
│                  │ └─────────────────────────────┘ │
└──────────────────┴──────────────────────────────────┘
```

### Workflow

**1. Open Database**
- Menu: File → Open Database...
- Or: Click "Open Database" toolbar button
- Or: Pass database as command-line argument

**2. Browse Taxonomy**
- Click to expand kingdoms, divisions, classes, etc.
- Navigate hierarchically through the tree
- Lazy-loaded for performance with large databases

**3. Search**
- Type scientific name (e.g., "Arabidopsis")
- Type common name (e.g., "tomato")
- Press Enter or click Search
- Click any result to view details

**4. View Details**
- Click any taxon in the browser
- See complete information in Details tab
- View lineage from Kingdom to Species
- See all common names
- Browse child taxa

**5. Visualize**
- Select a taxon
- Switch to Visualization tab
- See color-coded lineage graph
- Save visualization as image

**6. Statistics**
- Switch to Statistics tab
- See database overview
- View taxa counts by rank
- Click Refresh for updates

## Database Population

### Default Species List

The `populate_database.py` script includes ~33 diverse species:

**Trees:**
- Quercus alba (White oak)
- Acer saccharum (Sugar maple)
- Sequoia sempervirens (Coast redwood)

**Flowers:**
- Rosa rugosa (Rugosa rose)
- Tulipa gesneriana (Garden tulip)
- Helianthus annuus (Sunflower)

**Crops:**
- Solanum lycopersicum (Tomato)
- Zea mays (Corn)
- Triticum aestivum (Wheat)

**Model Organisms:**
- Arabidopsis thaliana (Thale cress)
- Nicotiana tabacum (Tobacco)

**Medicinal Plants:**
- Ginkgo biloba (Maidenhair tree)
- Echinacea purpurea (Purple coneflower)
- Salvia officinalis (Common sage)

**...and more**

### Customizing Species List

Edit `populate_database.py` to add your own species:

```python
PLANT_SPECIES = [
    ("Genus species", "Common name"),
    ("Pinus contorta", "Lodgepole pine"),
    # Add your species here
]
```

### Population Options

```bash
# Populate with all species
python populate_database.py --db myplants.db

# Limit to N species (for testing)
python populate_database.py --db test.db --max 5

# Verbose output
python populate_database.py --db plants.db --verbose
```

## Visualization Features

### Linear Lineage View

Shows taxonomic hierarchy as connected nodes:

```
Kingdom → Division → Class → Order → Family → Genus → Species
```

**Color Coding:**
- 🟢 Kingdom - Green
- 🔵 Division/Phylum - Blue
- 🟣 Class - Purple
- 🔴 Order - Red
- 🟠 Family - Orange
- 🔷 Genus - Turquoise
- 🟧 Species - Dark Orange

### Saving Visualizations

1. Select a taxon
2. Go to Visualization tab
3. Click "Save Image"
4. Choose format: PNG, PDF, or SVG
5. High resolution (300 DPI)

## Keyboard Shortcuts

- **Ctrl+O** - Open Database
- **Ctrl+Q** - Quit Application
- **Enter** - Search (when in search box)

## Tips & Tricks

### Performance

**Large Databases:**
- Tree nodes load lazily (only when expanded)
- Search limited to 100 results
- Statistics cached until refresh

**Slow Searches:**
- Database size affects search speed
- Consider limiting population to relevant taxa
- Use specific search terms

### Best Practices

**Database Files:**
- Keep databases under 50MB for best performance
- Use separate databases for different projects
- Backup populated databases

**Search:**
- Use partial names: "Arab" finds "Arabidopsis"
- Common names work: "rose" finds Rosa species
- Case-insensitive search

### Troubleshooting

**GUI Won't Start:**
```bash
# Check PyQt5 installation
python -c "from PyQt5.QtWidgets import QApplication"

# Reinstall if needed
pip install --upgrade PyQt5
```

**Visualization Blank:**
```bash
# Check matplotlib
python -c "import matplotlib; print(matplotlib.__version__)"

# May need backend setup
pip install --upgrade matplotlib
```

**Database Not Loading:**
- Verify file exists and has .db extension
- Check file permissions
- Try opening with `sqlite3` command line

**Search Not Working:**
- Database must be loaded first
- Check status bar for "Database loaded"
- Verify database contains data

## Command Line Usage

```bash
# Basic launch
python taxonomy_gui.py

# Auto-load database
python taxonomy_gui.py plants.db

# From different directory
python /path/to/taxonomy_gui.py /path/to/database.db
```

## Example Session

```bash
# 1. Populate database with 10 species for quick testing
python populate_database.py --db test.db --max 10 --verbose

# Output shows:
# [1/10] Quercus alba (White oak)
#     Found in ITIS (ID: 19290)
#     ✓ Stored 7 taxa
# ...
# Results:
#   Successful: 10/10
#   Total taxa: 70 (+70)

# 2. Launch GUI with this database
python taxonomy_gui.py test.db

# 3. In GUI:
#    - Expand Plantae → Tracheophyta → Magnoliopsida
#    - Search for "Quercus"
#    - Click on Quercus alba
#    - View lineage in Visualization tab
#    - Save image as oak_lineage.png
```

## Advanced Features

### Multiple Databases

Open different databases to compare:
- File → Open Database...
- Switch between databases as needed
- Each database independent

### Extending the GUI

The code is modular and extensible:

**Add Custom Widgets:**
```python
from PyQt5.QtWidgets import QWidget

class MyCustomWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Your code here
        
# Add to main window tabs
custom_widget = MyCustomWidget()
right_tabs.addTab(custom_widget, "Custom")
```

**Add Menu Items:**
```python
def create_menus(self):
    # ... existing menus ...
    
    tools_menu = menubar.addMenu('Tools')
    export_action = QAction('Export to CSV', self)
    export_action.triggered.connect(self.export_csv)
    tools_menu.addAction(export_action)
```

## Integration with FLIKA

Given your FLIKA experience, here's how this GUI compares:

**Similarities:**
- PyQt5-based architecture
- Modular widget design
- Matplotlib integration for visualization
- Database-backed data management

**Reusable Patterns:**
- Widget structure follows FLIKA conventions
- Signal/slot connections
- Matplotlib canvas in PyQt
- Multi-tab interface

**Potential Integration:**
- Could be a FLIKA plugin
- Share visualization techniques
- Similar data browsing patterns

## Logging

GUI actions are logged to:
- Console (INFO level)
- Log files in `logs/` directory

Enable verbose for debugging:
```python
from utils.logger import setup_quick_logging
setup_quick_logging(verbose=True)
```

## Future Enhancements

Possible additions:
- [ ] Export to CSV/Excel
- [ ] Import from additional databases
- [ ] Advanced filtering
- [ ] Phylogenetic tree view
- [ ] Image gallery integration
- [ ] Geographic distribution maps
- [ ] Batch export capabilities

## Credits

Built with:
- **PyQt5** - GUI framework
- **matplotlib** - Scientific visualization
- **SQLite** - Database engine
- **ITIS & GBIF** - Taxonomy data sources
