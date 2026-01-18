"""
Taxonomy visualization widgets using matplotlib.

Provides graphical tree visualization of taxonomic hierarchies.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from database.db_manager import TaxonomyDatabase
from utils.logger import get_logger

logger = get_logger('plant_taxonomy.viz')


class TaxonomyTreeCanvas(FigureCanvas):
    """Matplotlib canvas for drawing taxonomy trees."""
    
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(10, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        
    def plot_tree(self, lineage, title="Taxonomic Lineage"):
        """
        Plot taxonomic lineage as a tree.
        
        Args:
            lineage: List of taxon dictionaries from kingdom to species
            title: Plot title
        """
        self.ax.clear()
        
        if not lineage:
            self.ax.text(0.5, 0.5, 'No data to display', 
                        ha='center', va='center', fontsize=14)
            self.draw()
            return
        
        # Calculate positions
        n = len(lineage)
        x_positions = list(range(n))
        y_positions = [0] * n
        
        # Colors for different ranks
        rank_colors = {
            'Kingdom': '#2ecc71',
            'Division': '#3498db', 
            'Phylum': '#3498db',
            'Class': '#9b59b6',
            'Order': '#e74c3c',
            'Family': '#f39c12',
            'Genus': '#1abc9c',
            'Species': '#e67e22',
            'Subspecies': '#95a5a6',
            'Variety': '#7f8c8d'
        }
        
        # Plot nodes
        for i, taxon in enumerate(lineage):
            rank = taxon['rank']
            color = rank_colors.get(rank, '#34495e')
            
            # Draw node
            self.ax.scatter(x_positions[i], y_positions[i], 
                          s=1000, c=color, alpha=0.7, 
                          edgecolors='black', linewidths=2, zorder=2)
            
            # Add text
            name = taxon['scientific_name']
            # Wrap long names
            if len(name) > 15:
                words = name.split()
                if len(words) > 1:
                    name = '\n'.join([' '.join(words[:len(words)//2]),
                                    ' '.join(words[len(words)//2:])])
            
            self.ax.text(x_positions[i], y_positions[i], 
                        f"{name}\n({rank})",
                        ha='center', va='center', 
                        fontsize=9, fontweight='bold', zorder=3)
        
        # Draw connections
        for i in range(len(lineage) - 1):
            self.ax.plot([x_positions[i], x_positions[i+1]], 
                        [y_positions[i], y_positions[i+1]],
                        'k-', linewidth=2, alpha=0.5, zorder=1)
        
        # Styling
        self.ax.set_xlim(-0.5, n - 0.5)
        self.ax.set_ylim(-1, 1)
        self.ax.axis('off')
        self.ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        self.fig.tight_layout()
        self.draw()
        
        logger.debug(f"Plotted tree with {n} taxa")


class TaxonomyVisualizationWidget(QWidget):
    """Widget for visualizing taxonomy trees."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        self.current_tsn = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)
        
        # Control panel
        controls = QHBoxLayout()
        
        self.info_label = QLabel("Select a taxon to visualize its lineage")
        self.info_label.setStyleSheet("font-size: 11pt; color: gray;")
        controls.addWidget(self.info_label)
        
        controls.addStretch()
        
        self.save_btn = QPushButton("Save Image")
        self.save_btn.clicked.connect(self.save_image)
        self.save_btn.setEnabled(False)
        controls.addWidget(self.save_btn)
        
        layout.addLayout(controls)
        
        # Matplotlib canvas
        self.canvas = TaxonomyTreeCanvas(self)
        layout.addWidget(self.canvas)
        
        # Navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        
    def set_database(self, db_path: str):
        """Set database for queries."""
        try:
            self.db = TaxonomyDatabase(db_path)
            self.db.connect()
            logger.info(f"Visualization database set: {db_path}")
        except Exception as e:
            logger.error(f"Failed to set database: {e}")
            
    def show_taxon_lineage(self, taxon_data: dict):
        """Show lineage visualization for a taxon."""
        if not self.db:
            return
            
        try:
            # Use database ID if TSN is not available (for GBIF data)
            taxon_id = taxon_data.get('tsn') or taxon_data.get('id')
            
            if not taxon_id:
                logger.warning("No valid identifier found for taxon")
                return
                
            self.current_tsn = taxon_id
            
            # Get full lineage - use TSN if available, otherwise use ID
            if taxon_data.get('tsn'):
                lineage = self.db.get_lineage(taxon_data['tsn'])
            else:
                # For GBIF data, get lineage using database ID
                lineage = self.db.get_lineage_by_id(taxon_data['id'])
            
            if not lineage:
                logger.warning(f"No lineage found for taxon: {taxon_data['scientific_name']}")
                return
            
            # Update info label
            name = taxon_data['scientific_name']
            rank = taxon_data['rank']
            self.info_label.setText(f"Lineage: {name} ({rank})")
            self.info_label.setStyleSheet("font-size: 11pt; color: black;")
            
            # Plot
            title = f"Taxonomic Lineage: {name}"
            self.canvas.plot_tree(lineage, title)
            
            self.save_btn.setEnabled(True)
            
            logger.info(f"Visualized lineage for: {name}")
            
        except Exception as e:
            logger.error(f"Failed to visualize taxon: {e}")
            
    def save_image(self):
        """Save current visualization to file."""
        from PyQt5.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Taxonomy Tree",
            "",
            "PNG Image (*.png);;PDF Document (*.pdf);;SVG Image (*.svg)"
        )
        
        if filename:
            try:
                self.canvas.fig.savefig(filename, dpi=300, bbox_inches='tight')
                logger.info(f"Saved visualization to: {filename}")
            except Exception as e:
                logger.error(f"Failed to save image: {e}")


class RadialTreeCanvas(FigureCanvas):
    """Matplotlib canvas for radial tree visualization."""
    
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(10, 10), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='polar')
        super().__init__(self.fig)
        self.setParent(parent)
        
    def plot_radial_tree(self, taxon_data, db, max_depth=3):
        """
        Plot taxonomy as radial tree showing parent and children.
        
        Args:
            taxon_data: Root taxon dictionary
            db: Database instance
            max_depth: Maximum depth to show
        """
        self.ax.clear()
        
        import numpy as np
        
        # Get lineage and children
        tsn = taxon_data['tsn']
        
        # Get children recursively
        def get_tree(parent_tsn, depth=0):
            if depth >= max_depth:
                return []
            children = db.get_children(parent_tsn)
            result = []
            for child in children[:20]:  # Limit to prevent overcrowding
                result.append({
                    'taxon': child,
                    'children': get_tree(child['tsn'], depth + 1)
                })
            return result
        
        tree_data = get_tree(tsn)
        
        if not tree_data:
            self.ax.text(0, 0, 'No children to display',
                        ha='center', va='center', fontsize=14)
            self.ax.set_rticks([])
            self.ax.set_xticklabels([])
            self.draw()
            return
        
        # Plot radial tree
        def plot_level(nodes, level, theta_start, theta_end):
            if not nodes:
                return
                
            n = len(nodes)
            theta_step = (theta_end - theta_start) / max(n, 1)
            
            for i, node in enumerate(nodes):
                theta = theta_start + i * theta_step + theta_step / 2
                r = level * 2
                
                # Plot node
                self.ax.plot(theta, r, 'o', markersize=10, 
                           color='steelblue', alpha=0.7)
                
                # Add label
                name = node['taxon']['scientific_name']
                if len(name) > 20:
                    name = name[:17] + '...'
                    
                rotation = np.degrees(theta) - 90
                if rotation > 90:
                    rotation -= 180
                    
                self.ax.text(theta, r + 0.3, name,
                           rotation=rotation, ha='center', va='bottom',
                           fontsize=8)
                
                # Draw connection to parent
                if level > 1:
                    parent_theta = (theta_start + theta_end) / 2
                    parent_r = (level - 1) * 2
                    self.ax.plot([parent_theta, theta], [parent_r, r],
                               'k-', alpha=0.3, linewidth=1)
                
                # Recurse for children
                if node['children']:
                    child_start = theta - theta_step / 2
                    child_end = theta + theta_step / 2
                    plot_level(node['children'], level + 1, 
                             child_start, child_end)
        
        # Center node
        self.ax.plot(0, 0, 'o', markersize=15, color='orange', alpha=0.8)
        self.ax.text(0, 0.5, taxon_data['scientific_name'],
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Plot tree
        plot_level(tree_data, 1, 0, 2 * np.pi)
        
        self.ax.set_ylim(0, max_depth * 2 + 1)
        self.ax.set_title(f"Radial Tree: {taxon_data['scientific_name']}",
                        fontsize=14, fontweight='bold', pad=20)
        self.ax.grid(True, alpha=0.3)
        
        self.fig.tight_layout()
        self.draw()
        
        logger.debug(f"Plotted radial tree for: {taxon_data['scientific_name']}")
