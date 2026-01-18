#!/usr/bin/env python3
"""
Plant Taxonomy Database GUI - Main Window

PyQt-based graphical interface for browsing and visualizing plant taxonomy.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QLabel, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QGroupBox,
    QMessageBox, QFileDialog, QStatusBar, QAction, QToolBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

from database.db_manager import TaxonomyDatabase
from models.taxonomy import Taxon
from utils.formatting import format_lineage, get_taxon_summary
from utils.logger import setup_quick_logging, get_logger
from gui.visualization import TaxonomyVisualizationWidget
from gui.comparative_viz import ComparativeVisualizationWidget

logger = get_logger('plant_taxonomy.gui')


class TaxonomyBrowserWidget(QWidget):
    """Widget for browsing taxonomic hierarchy."""
    
    taxon_selected = pyqtSignal(dict)  # Emits taxon data when selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        self.current_taxon = None  # Currently selected taxon
        self.comparative_widget = None  # Will be set by main window
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Enter scientific or common name...")
        self.search_box.returnPressed.connect(self.search_database)
        search_layout.addWidget(self.search_box)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_database)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
        
        # Add to comparison button
        compare_layout = QHBoxLayout()
        self.add_to_compare_btn = QPushButton("➕ Add to Comparison")
        self.add_to_compare_btn.clicked.connect(self.add_to_comparison)
        self.add_to_compare_btn.setEnabled(False)
        self.add_to_compare_btn.setToolTip("Add selected species to comparative view")
        compare_layout.addWidget(self.add_to_compare_btn)
        compare_layout.addStretch()
        
        layout.addLayout(compare_layout)
        
        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Rank", "Common Names"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 100)
        self.tree.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.tree)
        
        # Status label
        self.status_label = QLabel("No database loaded")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)
        
    def set_database(self, db_path: str):
        """Set the database to browse."""
        try:
            self.db = TaxonomyDatabase(db_path)
            self.db.connect()
            
            stats = self.db.get_statistics()
            self.status_label.setText(
                f"Database: {Path(db_path).name} - "
                f"{stats['total_taxa']} taxa, "
                f"{stats['total_common_names']} common names"
            )
            self.status_label.setStyleSheet("color: green;")
            
            # Load kingdoms
            self.load_kingdoms()
            
            logger.info(f"Database loaded: {db_path}")
            
        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load database:\n{e}")
            
    def load_kingdoms(self):
        """Load kingdoms as root items."""
        self.tree.clear()
        
        if not self.db:
            return
        
        try:
            # Get all kingdoms
            results = self.db.search_by_name("Plantae")
            kingdoms = [r for r in results if r['rank'] == 'Kingdom']
            
            for kingdom in kingdoms:
                item = QTreeWidgetItem(self.tree)
                item.setText(0, kingdom['scientific_name'])
                item.setText(1, kingdom['rank'])
                item.setData(0, Qt.UserRole, kingdom)
                
                # Add placeholder child to show expand arrow
                if self.has_children(kingdom):
                    placeholder = QTreeWidgetItem(item)
                    placeholder.setText(0, "Loading...")
                    
            self.tree.expandToDepth(0)
            
        except Exception as e:
            logger.error(f"Failed to load kingdoms: {e}")
            
    def has_children(self, taxon_data: dict) -> bool:
        """Check if taxon has children."""
        if not self.db:
            return False
        # Use TSN if available, otherwise use ID
        identifier = taxon_data.get('tsn') or taxon_data.get('id')
        if not identifier:
            return False
        children = self.db.get_children_by_taxon_data(taxon_data)
        return len(children) > 0
        
    def on_item_clicked(self, item, column):
        """Handle tree item click."""
        taxon_data = item.data(0, Qt.UserRole)
        if not taxon_data:
            return
            
        # Store current taxon
        self.current_taxon = taxon_data
        
        # Enable add to comparison button
        self.add_to_compare_btn.setEnabled(True)
        
        # Emit signal with taxon data
        self.taxon_selected.emit(taxon_data)
        
        # Load children if not already loaded
        if item.childCount() == 1:
            child = item.child(0)
            if child.text(0) == "Loading...":
                self.load_children(item, taxon_data)
                
    def add_to_comparison(self):
        """Add current taxon to comparative visualization."""
        if self.current_taxon and self.comparative_widget:
            self.comparative_widget.add_species(self.current_taxon)
                
    def load_children(self, parent_item, parent_data: dict):
        """Load children of a taxon."""
        if not self.db:
            return
            
        # Remove placeholder
        parent_item.takeChildren()
        
        try:
            children = self.db.get_children_by_taxon_data(parent_data)
            
            for child in children:
                item = QTreeWidgetItem(parent_item)
                item.setText(0, child['scientific_name'])
                item.setText(1, child['rank'])
                
                # Add common names if TSN available
                if child.get('tsn'):
                    common_names = self.db.get_common_names(child['tsn'])
                    if common_names:
                        item.setText(2, ", ".join(common_names[:3]))
                
                item.setData(0, Qt.UserRole, child)
                
                # Add placeholder if has children
                if self.has_children(child):
                    placeholder = QTreeWidgetItem(item)
                    placeholder.setText(0, "Loading...")
                    
        except Exception as e:
            logger.error(f"Failed to load children: {e}")
            
    def search_database(self):
        """Search database and display results."""
        if not self.db:
            QMessageBox.warning(self, "No Database", "Please load a database first")
            return
            
        query = self.search_box.text().strip()
        if not query:
            self.load_kingdoms()
            return
            
        try:
            results = self.db.search_by_name(query, limit=100)
            
            self.tree.clear()
            
            if not results:
                item = QTreeWidgetItem(self.tree)
                item.setText(0, "No results found")
                item.setForeground(0, Qt.gray)
                return
                
            # Display results
            for result in results:
                item = QTreeWidgetItem(self.tree)
                item.setText(0, result['scientific_name'])
                item.setText(1, result['rank'])
                
                # Add common names if TSN available
                if result.get('tsn'):
                    common_names = self.db.get_common_names(result['tsn'])
                    if common_names:
                        item.setText(2, ", ".join(common_names[:3]))
                
                item.setData(0, Qt.UserRole, result)
                
            self.status_label.setText(f"Found {len(results)} results")
            logger.info(f"Search '{query}' found {len(results)} results")
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            QMessageBox.critical(self, "Search Error", f"Search failed:\n{e}")


class TaxonDetailsWidget(QWidget):
    """Widget for displaying taxon details."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        self.title_label = QLabel("Taxon Details")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)
        
        # Details text
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        layout.addWidget(self.details_text)
        
        self.clear_details()
        
    def set_database(self, db_path: str):
        """Set database for queries."""
        try:
            self.db = TaxonomyDatabase(db_path)
            self.db.connect()
        except Exception as e:
            logger.error(f"Failed to set database: {e}")
            
    def show_taxon(self, taxon_data: dict):
        """Display taxon details."""
        if not self.db:
            return
            
        try:
            # Update title
            name = taxon_data['scientific_name']
            rank = taxon_data['rank']
            self.title_label.setText(f"{name} ({rank})")
            
            # Build details HTML
            html = "<html><body>"
            html += f"<h2>{name}</h2>"
            html += f"<p><b>Rank:</b> {rank}</p>"
            
            # Authorship
            if taxon_data.get('authorship'):
                html += f"<p><b>Authority:</b> {taxon_data['authorship']}</p>"
            
            # Identifier (TSN or database ID)
            if taxon_data.get('tsn'):
                html += f"<p><b>TSN:</b> {taxon_data['tsn']}</p>"
            elif taxon_data.get('id'):
                html += f"<p><b>Database ID:</b> {taxon_data['id']}</p>"
            
            # Source
            if taxon_data.get('source'):
                html += f"<p><b>Source:</b> {taxon_data['source']}</p>"
            
            # Common names (only if TSN available)
            if taxon_data.get('tsn'):
                common_names = self.db.get_common_names(taxon_data['tsn'])
                if common_names:
                    html += "<p><b>Common Names:</b></p><ul>"
                    for cn in common_names[:10]:
                        html += f"<li>{cn}</li>"
                    html += "</ul>"
            
            # Lineage
            if taxon_data.get('tsn'):
                lineage = self.db.get_lineage(taxon_data['tsn'])
            else:
                lineage = self.db.get_lineage_by_id(taxon_data['id'])
                
            if lineage:
                html += "<p><b>Taxonomic Lineage:</b></p>"
                html += "<table cellpadding='3'>"
                for taxon in lineage:
                    html += f"<tr><td><i>{taxon['rank']}:</i></td><td><b>{taxon['scientific_name']}</b></td></tr>"
                html += "</table>"
            
            # Children
            children = self.db.get_children_by_taxon_data(taxon_data)
            if children:
                html += f"<p><b>Children ({len(children)}):</b></p><ul>"
                for child in children[:20]:
                    html += f"<li>{child['scientific_name']} ({child['rank']})</li>"
                if len(children) > 20:
                    html += f"<li><i>... and {len(children) - 20} more</i></li>"
                html += "</ul>"
            
            html += "</body></html>"
            
            self.details_text.setHtml(html)
            
            logger.debug(f"Showing details for: {name}")
            
        except Exception as e:
            logger.error(f"Failed to show taxon details: {e}")
            self.details_text.setPlainText(f"Error displaying details:\n{e}")
            
    def clear_details(self):
        """Clear details view."""
        self.title_label.setText("Taxon Details")
        self.details_text.setHtml(
            "<html><body><p style='color:gray;font-style:italic;'>"
            "Select a taxon from the browser to view details"
            "</p></body></html>"
        )


class StatisticsWidget(QWidget):
    """Widget for displaying database statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Database Statistics")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Statistics text
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Statistics")
        self.refresh_btn.clicked.connect(self.refresh_statistics)
        layout.addWidget(self.refresh_btn)
        
    def set_database(self, db_path: str):
        """Set database for queries."""
        try:
            self.db = TaxonomyDatabase(db_path)
            self.db.connect()
            self.refresh_statistics()
        except Exception as e:
            logger.error(f"Failed to set database: {e}")
            
    def refresh_statistics(self):
        """Refresh statistics display."""
        if not self.db:
            return
            
        try:
            stats = self.db.get_statistics()
            
            html = "<html><body>"
            html += "<h3>Overview</h3>"
            html += f"<p><b>Total Taxa:</b> {stats['total_taxa']}</p>"
            html += f"<p><b>Common Names:</b> {stats['total_common_names']}</p>"
            
            if stats.get('by_rank'):
                html += "<h3>Taxa by Rank</h3>"
                html += "<table cellpadding='5' border='1'>"
                html += "<tr><th>Rank</th><th>Count</th></tr>"
                
                for rank, count in sorted(stats['by_rank'].items(), 
                                        key=lambda x: x[1], reverse=True):
                    html += f"<tr><td>{rank}</td><td>{count}</td></tr>"
                    
                html += "</table>"
            
            html += "</body></html>"
            
            self.stats_text.setHtml(html)
            
            logger.info("Statistics refreshed")
            
        except Exception as e:
            logger.error(f"Failed to refresh statistics: {e}")
            self.stats_text.setPlainText(f"Error loading statistics:\n{e}")


class PlantTaxonomyGUI(QMainWindow):
    """Main window for plant taxonomy database GUI."""
    
    def __init__(self):
        super().__init__()
        self.db_path = None
        self.init_ui()
        setup_quick_logging(verbose=False)
        logger.info("GUI initialized")
        
    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("Plant Taxonomy Database Browser")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create menu bar
        self.create_menus()
        
        # Create toolbar
        self.create_toolbar()
        
        # Central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Browser
        self.browser = TaxonomyBrowserWidget()
        self.browser.taxon_selected.connect(self.on_taxon_selected)
        splitter.addWidget(self.browser)
        
        # Right: Tabs for details and statistics
        right_tabs = QTabWidget()
        
        self.details = TaxonDetailsWidget()
        right_tabs.addTab(self.details, "Details")
        
        self.statistics = StatisticsWidget()
        right_tabs.addTab(self.statistics, "Statistics")
        
        self.visualization = TaxonomyVisualizationWidget()
        right_tabs.addTab(self.visualization, "Visualization")
        
        self.comparative = ComparativeVisualizationWidget()
        right_tabs.addTab(self.comparative, "Compare Species")
        
        splitter.addWidget(right_tabs)
        
        splitter.setSizes([600, 600])
        
        layout.addWidget(splitter)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready - Please open a database")
        
    def create_menus(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open Database...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_database)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction('Quit', self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        open_action = QAction('Open Database', self)
        open_action.triggered.connect(self.open_database)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        refresh_action = QAction('Refresh', self)
        refresh_action.triggered.connect(self.refresh_all)
        toolbar.addAction(refresh_action)
        
    def open_database(self):
        """Open database file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Plant Taxonomy Database",
            "",
            "Database Files (*.db);;All Files (*)"
        )
        
        if filename:
            self.load_database(filename)
            
    def load_database(self, db_path: str):
        """Load database into GUI."""
        try:
            self.db_path = db_path
            
            # Set database for all widgets
            self.browser.set_database(db_path)
            self.details.set_database(db_path)
            self.statistics.set_database(db_path)
            self.visualization.set_database(db_path)
            self.comparative.set_database(db_path)
            
            # Connect browser to comparative widget
            self.browser.comparative_widget = self.comparative
            
            self.statusBar.showMessage(f"Loaded: {Path(db_path).name}")
            logger.info(f"Database loaded: {db_path}")
            
        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load database:\n{e}")
            
    def on_taxon_selected(self, taxon_data: dict):
        """Handle taxon selection."""
        self.details.show_taxon(taxon_data)
        self.visualization.show_taxon_lineage(taxon_data)
        name = taxon_data['scientific_name']
        rank = taxon_data['rank']
        self.statusBar.showMessage(f"Selected: {name} ({rank})")
        
    def refresh_all(self):
        """Refresh all views."""
        if self.db_path:
            self.browser.load_kingdoms()
            self.statistics.refresh_statistics()
            self.statusBar.showMessage("Refreshed")
            
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Plant Taxonomy Database",
            "Plant Taxonomy Database Browser\n\n"
            "A comprehensive tool for exploring plant taxonomy data from "
            "ITIS and GBIF databases.\n\n"
            "Features:\n"
            "• Browse taxonomic hierarchy\n"
            "• Search by scientific or common names\n"
            "• View detailed taxon information\n"
            "• Visualize individual lineages\n"
            "• Compare multiple species relationships\n"
            "• Database statistics\n\n"
            "Built with PyQt5"
        )


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    gui = PlantTaxonomyGUI()
    
    # Auto-load database if provided as argument
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        if Path(db_path).exists():
            gui.load_database(db_path)
    
    gui.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
