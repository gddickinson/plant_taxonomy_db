#!/usr/bin/env python3
"""
Plant Taxonomy Database GUI - Main Window

PyQt-based graphical interface for browsing and visualizing plant taxonomy.
Widget implementations are in gui/browser_widget.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QSplitter, QTabWidget,
    QMessageBox, QFileDialog, QStatusBar, QAction, QToolBar
)
from PyQt5.QtCore import Qt

from gui.browser_widget import (
    TaxonomyBrowserWidget,
    TaxonDetailsWidget,
    StatisticsWidget,
)
from gui.visualization import TaxonomyVisualizationWidget
from gui.comparative_viz import ComparativeVisualizationWidget
from utils.logger import setup_quick_logging, get_logger

logger = get_logger('plant_taxonomy.gui')


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
            "- Browse taxonomic hierarchy\n"
            "- Search by scientific or common names\n"
            "- View detailed taxon information\n"
            "- Visualize individual lineages\n"
            "- Compare multiple species relationships\n"
            "- Database statistics\n\n"
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
