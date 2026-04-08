"""
Taxonomy browser and details widgets for the Plant Taxonomy GUI.

Contains the tree-based browser, taxon details view, and statistics panel.
"""

from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QTextEdit,
    QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from database.db_manager import TaxonomyDatabase
from models.taxonomy import Taxon
from utils.formatting import format_lineage, get_taxon_summary
from utils.logger import get_logger

logger = get_logger('plant_taxonomy.gui')


class TaxonomyBrowserWidget(QWidget):
    """Widget for browsing taxonomic hierarchy."""

    taxon_selected = pyqtSignal(dict)  # Emits taxon data when selected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        self.current_taxon = None
        self.comparative_widget = None
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
        self.add_to_compare_btn = QPushButton("+ Add to Comparison")
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
            results = self.db.search_by_name("Plantae")
            kingdoms = [r for r in results if r['rank'] == 'Kingdom']

            for kingdom in kingdoms:
                item = QTreeWidgetItem(self.tree)
                item.setText(0, kingdom['scientific_name'])
                item.setText(1, kingdom['rank'])
                item.setData(0, Qt.UserRole, kingdom)

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

        self.current_taxon = taxon_data
        self.add_to_compare_btn.setEnabled(True)
        self.taxon_selected.emit(taxon_data)

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

        parent_item.takeChildren()

        try:
            children = self.db.get_children_by_taxon_data(parent_data)

            for child in children:
                item = QTreeWidgetItem(parent_item)
                item.setText(0, child['scientific_name'])
                item.setText(1, child['rank'])

                if child.get('tsn'):
                    common_names = self.db.get_common_names(child['tsn'])
                    if common_names:
                        item.setText(2, ", ".join(common_names[:3]))

                item.setData(0, Qt.UserRole, child)

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

            for result in results:
                item = QTreeWidgetItem(self.tree)
                item.setText(0, result['scientific_name'])
                item.setText(1, result['rank'])

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

        self.title_label = QLabel("Taxon Details")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)

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
            name = taxon_data['scientific_name']
            rank = taxon_data['rank']
            self.title_label.setText(f"{name} ({rank})")

            html = "<html><body>"
            html += f"<h2>{name}</h2>"
            html += f"<p><b>Rank:</b> {rank}</p>"

            if taxon_data.get('authorship'):
                html += f"<p><b>Authority:</b> {taxon_data['authorship']}</p>"

            if taxon_data.get('tsn'):
                html += f"<p><b>TSN:</b> {taxon_data['tsn']}</p>"
            elif taxon_data.get('id'):
                html += f"<p><b>Database ID:</b> {taxon_data['id']}</p>"

            if taxon_data.get('source'):
                html += f"<p><b>Source:</b> {taxon_data['source']}</p>"

            if taxon_data.get('tsn'):
                common_names = self.db.get_common_names(taxon_data['tsn'])
                if common_names:
                    html += "<p><b>Common Names:</b></p><ul>"
                    for cn in common_names[:10]:
                        html += f"<li>{cn}</li>"
                    html += "</ul>"

            if taxon_data.get('tsn'):
                lineage = self.db.get_lineage(taxon_data['tsn'])
            else:
                lineage = self.db.get_lineage_by_id(taxon_data['id'])

            if lineage:
                html += "<p><b>Taxonomic Lineage:</b></p>"
                html += "<table cellpadding='3'>"
                for taxon in lineage:
                    html += f"<tr><td><i>{taxon['rank']}:</i></td>"
                    html += f"<td><b>{taxon['scientific_name']}</b></td></tr>"
                html += "</table>"

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

        title = QLabel("Database Statistics")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)

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
