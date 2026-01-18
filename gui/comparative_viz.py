"""
Comparative taxonomy visualization - shows relationships between multiple species.

Displays phylogenetic-style trees showing common ancestors and divergence points.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QListWidget, QListWidgetItem, QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

from database.db_manager import TaxonomyDatabase
from utils.logger import get_logger

logger = get_logger('plant_taxonomy.viz.comparative')


class ComparativeTreeCanvas(FigureCanvas):
    """Canvas for drawing comparative phylogenetic-style trees."""
    
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        
    def plot_comparative_tree(self, species_lineages, species_names):
        """
        Plot comparative tree showing relationships between species.
        
        Args:
            species_lineages: List of lineages (each lineage is a list of taxa)
            species_names: List of species names for labeling
        """
        self.ax.clear()
        
        if not species_lineages:
            self.ax.text(0.5, 0.5, 'Select species to compare', 
                        ha='center', va='center', fontsize=14)
            self.draw()
            return
        
        # Find common ancestor and build tree structure
        tree_data = self._build_tree_structure(species_lineages, species_names)
        
        # Calculate positions
        positions = self._calculate_positions(tree_data)
        
        # Draw tree
        self._draw_tree(tree_data, positions)
        
        self.ax.axis('off')
        self.ax.set_title('Comparative Taxonomic Relationships', 
                         fontsize=14, fontweight='bold', pad=20)
        
        self.fig.tight_layout()
        self.draw()
        
        logger.info(f"Plotted comparative tree with {len(species_names)} species")
        
    def _build_tree_structure(self, species_lineages, species_names):
        """Build tree structure from lineages."""
        # Create a tree structure showing relationships
        tree = {'name': 'root', 'children': [], 'rank': None, 'species': []}
        
        for i, lineage in enumerate(species_lineages):
            current = tree
            
            for taxon in lineage:
                # Ensure taxon is a dict
                if not isinstance(taxon, dict):
                    taxon = dict(taxon)
                
                name = taxon.get('scientific_name', 'Unknown')
                rank = taxon.get('rank', 'Unknown')
                
                # Find or create node for this taxon
                child = None
                for c in current['children']:
                    if c['name'] == name:
                        child = c
                        break
                
                if not child:
                    child = {
                        'name': name,
                        'rank': rank,
                        'children': [],
                        'species': []
                    }
                    current['children'].append(child)
                
                # If this is the final taxon (species), mark it
                if taxon == lineage[-1]:
                    child['species'].append(species_names[i])
                
                current = child
        
        return tree
    
    def _calculate_positions(self, tree, x=0, y=0, x_spacing=2.0, y_spacing=1.0, positions=None):
        """Calculate x,y positions for all nodes."""
        if positions is None:
            positions = {}
        
        name = tree.get('name')
        if not name:
            return x, x
        
        children = tree.get('children', [])
        
        if not children:
            # Leaf node
            positions[name] = (x, y)
            return x, x
        
        # Internal node - position based on children
        child_positions = []
        current_x = x
        
        for i, child in enumerate(children):
            min_x, max_x = self._calculate_positions(
                child, current_x, y - y_spacing, x_spacing, y_spacing, positions
            )
            child_positions.append((min_x + max_x) / 2)
            current_x = max_x + x_spacing
        
        # Position this node at midpoint of children
        if child_positions:
            node_x = (child_positions[0] + child_positions[-1]) / 2
            positions[name] = (node_x, y)
            return child_positions[0], child_positions[-1]
        else:
            positions[name] = (x, y)
            return x, x
    
    def _draw_tree(self, tree, positions, parent_pos=None):
        """Draw the tree recursively."""
        if tree.get('name') == 'root':
            # Draw children of root
            for child in tree.get('children', []):
                self._draw_tree(child, positions)
            return
        
        name = tree.get('name', 'Unknown')
        if name not in positions:
            logger.warning(f"Position not found for node: {name}")
            return
            
        pos = positions[name]
        
        # Color by rank
        rank_colors = {
            'Kingdom': '#2ecc71',
            'Division': '#3498db',
            'Phylum': '#3498db',
            'Class': '#9b59b6',
            'Order': '#e74c3c',
            'Family': '#f39c12',
            'Genus': '#1abc9c',
            'Species': '#e67e22',
        }
        rank = tree.get('rank', 'Unknown')
        color = rank_colors.get(rank, '#34495e')
        
        # Draw node
        species_list = tree.get('species', [])
        if species_list:
            # Leaf node (species) - use different marker
            self.ax.scatter(pos[0], pos[1], s=800, c=color, 
                          marker='s', alpha=0.7, edgecolors='black', 
                          linewidths=2, zorder=3)
        else:
            # Internal node
            self.ax.scatter(pos[0], pos[1], s=600, c=color, 
                          alpha=0.7, edgecolors='black', 
                          linewidths=2, zorder=3)
        
        # Add label
        if len(name) > 20:
            name = name[:17] + '...'
        
        # For species, show the species name below
        if species_list:
            label = f"{name}\n({rank})\n" + '\n'.join(species_list)
            fontsize = 8
        else:
            label = f"{name}\n({rank})"
            fontsize = 9
        
        self.ax.text(pos[0], pos[1], label,
                    ha='center', va='center', 
                    fontsize=fontsize, fontweight='bold', zorder=4)
        
        # Draw connections to children
        for child in tree.get('children', []):
            child_name = child.get('name')
            if child_name not in positions:
                continue
                
            child_pos = positions[child_name]
            
            # Draw L-shaped connection
            mid_y = (pos[1] + child_pos[1]) / 2
            
            self.ax.plot([pos[0], pos[0]], [pos[1], mid_y],
                        'k-', linewidth=2, alpha=0.5, zorder=1)
            self.ax.plot([pos[0], child_pos[0]], [mid_y, mid_y],
                        'k-', linewidth=2, alpha=0.5, zorder=1)
            self.ax.plot([child_pos[0], child_pos[0]], [mid_y, child_pos[1]],
                        'k-', linewidth=2, alpha=0.5, zorder=1)
            
            # Recurse
            self._draw_tree(child, positions, pos)


class ComparativeVisualizationWidget(QWidget):
    """Widget for comparing multiple species."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        self.selected_species = []  # List of taxon_data dicts
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface."""
        layout = QHBoxLayout(self)
        
        # Left panel - species selection
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        left_layout.addWidget(QLabel("<b>Selected Species:</b>"))
        
        self.species_list = QListWidget()
        self.species_list.setMaximumWidth(250)
        left_layout.addWidget(self.species_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_species)
        btn_layout.addWidget(self.clear_btn)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(self.remove_btn)
        
        left_layout.addLayout(btn_layout)
        
        self.compare_btn = QPushButton("Compare Species")
        self.compare_btn.clicked.connect(self.update_visualization)
        self.compare_btn.setEnabled(False)
        left_layout.addWidget(self.compare_btn)
        
        # Info label
        self.info_label = QLabel("Click species in the browser\nto add them here")
        self.info_label.setStyleSheet("color: gray; font-style: italic;")
        self.info_label.setWordWrap(True)
        left_layout.addWidget(self.info_label)
        
        left_layout.addStretch()
        
        # Right panel - visualization
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Control bar
        controls = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Image")
        self.save_btn.clicked.connect(self.save_image)
        self.save_btn.setEnabled(False)
        controls.addWidget(self.save_btn)
        
        controls.addStretch()
        
        right_layout.addLayout(controls)
        
        # Canvas
        self.canvas = ComparativeTreeCanvas(self)
        right_layout.addWidget(self.canvas)
        
        # Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        right_layout.addWidget(self.toolbar)
        
        # Add panels to splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 750])
        
        layout.addWidget(splitter)
        
    def set_database(self, db_path: str):
        """Set database for queries."""
        try:
            self.db = TaxonomyDatabase(db_path)
            self.db.connect()
            logger.info(f"Comparative visualization database set: {db_path}")
        except Exception as e:
            logger.error(f"Failed to set database: {e}")
            
    def add_species(self, taxon_data: dict):
        """Add a species to the comparison."""
        # Only add if it's a species rank
        if taxon_data['rank'] not in ['Species', 'Subspecies', 'Variety']:
            QMessageBox.information(
                self,
                "Not a Species",
                f"Please select a species-level taxon.\n'{taxon_data['scientific_name']}' is a {taxon_data['rank']}."
            )
            return
        
        # Check if already added
        for species in self.selected_species:
            if species['scientific_name'] == taxon_data['scientific_name']:
                return
        
        # Add to list
        self.selected_species.append(taxon_data)
        
        # Update UI
        item = QListWidgetItem(taxon_data['scientific_name'])
        self.species_list.addItem(item)
        
        self.compare_btn.setEnabled(len(self.selected_species) >= 2)
        
        logger.info(f"Added species: {taxon_data['scientific_name']}")
        
    def remove_selected(self):
        """Remove selected species from list."""
        current = self.species_list.currentRow()
        if current >= 0:
            self.species_list.takeItem(current)
            del self.selected_species[current]
            
            self.compare_btn.setEnabled(len(self.selected_species) >= 2)
            
    def clear_species(self):
        """Clear all species."""
        self.species_list.clear()
        self.selected_species.clear()
        self.compare_btn.setEnabled(False)
        self.canvas.ax.clear()
        self.canvas.ax.text(0.5, 0.5, 'Select species to compare',
                           ha='center', va='center', fontsize=14)
        self.canvas.draw()
        
    def update_visualization(self):
        """Update the comparative visualization."""
        if not self.db or len(self.selected_species) < 2:
            return
        
        try:
            # Get lineages for all selected species
            lineages = []
            names = []
            
            for species in self.selected_species:
                if species.get('tsn'):
                    lineage = self.db.get_lineage(species['tsn'])
                else:
                    lineage = self.db.get_lineage_by_id(species['id'])
                
                # Convert to list of dicts if needed
                if lineage:
                    # Ensure each item is a dict
                    lineage_dicts = []
                    for item in lineage:
                        if isinstance(item, dict):
                            lineage_dicts.append(item)
                        else:
                            # If it's a Row or tuple, convert to dict
                            lineage_dicts.append(dict(item))
                    
                    lineages.append(lineage_dicts)
                    names.append(species['scientific_name'])
            
            if not lineages:
                logger.warning("No lineages found for selected species")
                return
            
            # Plot
            self.canvas.plot_comparative_tree(lineages, names)
            self.save_btn.setEnabled(True)
            
            # Update info
            self.info_label.setText(
                f"Comparing {len(names)} species\n"
                f"Click 'Save Image' to export"
            )
            self.info_label.setStyleSheet("color: black;")
            
            logger.info(f"Updated comparative visualization with {len(names)} species")
            
        except Exception as e:
            logger.error(f"Failed to update visualization: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(
                self,
                "Visualization Error",
                f"Failed to create visualization:\n{e}"
            )
            
    def save_image(self):
        """Save current visualization."""
        from PyQt5.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Comparative Tree",
            "comparative_tree.png",
            "PNG Image (*.png);;PDF Document (*.pdf);;SVG Image (*.svg)"
        )
        
        if filename:
            try:
                self.canvas.fig.savefig(filename, dpi=300, bbox_inches='tight')
                logger.info(f"Saved comparative visualization to: {filename}")
                QMessageBox.information(
                    self,
                    "Saved",
                    f"Visualization saved to:\n{filename}"
                )
            except Exception as e:
                logger.error(f"Failed to save image: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
