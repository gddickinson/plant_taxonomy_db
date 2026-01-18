"""
Database manager for plant taxonomy data.

Handles SQLite database creation, schema management, and CRUD operations
for taxonomic data from various sources (ITIS, USDA, etc.)
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class TaxonomyDatabase:
    """Manages the plant taxonomy SQLite database."""
    
    def __init__(self, db_path: str = "plant_taxonomy.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        
    def connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        
    def create_schema(self):
        """Create database schema for taxonomy data."""
        
        # Main taxa table with hierarchical structure
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS taxa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tsn INTEGER UNIQUE,  -- Taxonomic Serial Number (ITIS)
                kingdom VARCHAR(100),
                division VARCHAR(100),  -- Sometimes called Phylum
                class VARCHAR(100),
                order_name VARCHAR(100),  -- 'order' is SQL keyword
                family VARCHAR(100),
                genus VARCHAR(100),
                species VARCHAR(100),
                subspecies VARCHAR(100),
                variety VARCHAR(100),
                rank VARCHAR(50),  -- Kingdom, Family, Species, etc.
                scientific_name TEXT NOT NULL,
                authorship TEXT,
                parent_tsn INTEGER,
                taxonomic_status VARCHAR(50),  -- accepted, synonym, invalid, etc.
                source VARCHAR(50),  -- ITIS, USDA, etc.
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_tsn) REFERENCES taxa(tsn)
            )
        """)
        
        # Common names table (one-to-many relationship)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS common_names (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tsn INTEGER NOT NULL,
                common_name TEXT NOT NULL,
                language VARCHAR(10) DEFAULT 'en',
                FOREIGN KEY (tsn) REFERENCES taxa(tsn)
            )
        """)
        
        # Synonyms table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS synonyms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accepted_tsn INTEGER NOT NULL,
                synonym_tsn INTEGER NOT NULL,
                synonym_name TEXT NOT NULL,
                synonym_author TEXT,
                FOREIGN KEY (accepted_tsn) REFERENCES taxa(tsn)
            )
        """)
        
        # Create indexes for common queries
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scientific_name 
            ON taxa(scientific_name)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_parent_tsn 
            ON taxa(parent_tsn)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rank 
            ON taxa(rank)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_kingdom 
            ON taxa(kingdom)
        """)
        
        self.conn.commit()
        
    def insert_taxon(self, taxon_data: Dict[str, Any]) -> int:
        """
        Insert a taxon into the database.
        
        Args:
            taxon_data: Dictionary containing taxon information
            
        Returns:
            Row ID of inserted taxon
        """
        columns = ', '.join(taxon_data.keys())
        placeholders = ', '.join(['?' for _ in taxon_data])
        
        query = f"INSERT OR REPLACE INTO taxa ({columns}) VALUES ({placeholders})"
        self.cursor.execute(query, list(taxon_data.values()))
        self.conn.commit()
        
        return self.cursor.lastrowid
        
    def insert_common_name(self, tsn: int, common_name: str, language: str = 'en'):
        """Insert a common name for a taxon."""
        self.cursor.execute("""
            INSERT INTO common_names (tsn, common_name, language)
            VALUES (?, ?, ?)
        """, (tsn, common_name, language))
        self.conn.commit()
        
    def insert_synonym(self, accepted_tsn: int, synonym_tsn: int, 
                      synonym_name: str, synonym_author: str = None):
        """Insert a synonym relationship."""
        self.cursor.execute("""
            INSERT INTO synonyms (accepted_tsn, synonym_tsn, synonym_name, synonym_author)
            VALUES (?, ?, ?, ?)
        """, (accepted_tsn, synonym_tsn, synonym_name, synonym_author))
        self.conn.commit()
        
    def get_taxon_by_tsn(self, tsn: int) -> Optional[Dict[str, Any]]:
        """Get taxon by TSN."""
        self.cursor.execute("SELECT * FROM taxa WHERE tsn = ?", (tsn,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
        
    def search_by_name(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for taxa by scientific or common name.
        
        Args:
            search_term: Search string
            limit: Maximum results to return
            
        Returns:
            List of matching taxa
        """
        # Search scientific names
        self.cursor.execute("""
            SELECT DISTINCT t.* FROM taxa t
            WHERE t.scientific_name LIKE ?
            LIMIT ?
        """, (f'%{search_term}%', limit))
        
        results = [dict(row) for row in self.cursor.fetchall()]
        
        # Also search common names if we have room
        if len(results) < limit:
            self.cursor.execute("""
                SELECT DISTINCT t.* FROM taxa t
                JOIN common_names cn ON t.tsn = cn.tsn
                WHERE cn.common_name LIKE ?
                LIMIT ?
            """, (f'%{search_term}%', limit - len(results)))
            
            results.extend([dict(row) for row in self.cursor.fetchall()])
            
        return results
        
    def get_lineage(self, tsn: int) -> List[Dict[str, Any]]:
        """
        Get full taxonomic lineage for a taxon.
        
        Args:
            tsn: Taxonomic Serial Number
            
        Returns:
            List of taxa from kingdom to species
        """
        lineage = []
        current_tsn = tsn
        
        while current_tsn:
            taxon = self.get_taxon_by_tsn(current_tsn)
            if not taxon:
                break
                
            lineage.insert(0, taxon)  # Add to front of list
            current_tsn = taxon.get('parent_tsn')
            
        return lineage
        
    def get_lineage_by_id(self, db_id: int) -> List[Dict[str, Any]]:
        """
        Get full taxonomic lineage for a taxon by database ID.
        
        Args:
            db_id: Database row ID
            
        Returns:
            List of taxa from kingdom to species
        """
        lineage = []
        
        # Get initial taxon by ID
        self.cursor.execute("SELECT * FROM taxa WHERE id = ?", (db_id,))
        row = self.cursor.fetchone()
        if not row:
            return lineage
            
        current_taxon = dict(row)
        
        # Build lineage by following parent_tsn chain
        # Note: For GBIF data, parent_tsn won't be set, so we need a different approach
        # We'll use the hierarchical fields instead
        lineage.append(current_taxon)
        
        # For taxa without proper parent_tsn, construct lineage from hierarchical fields
        if not current_taxon.get('parent_tsn'):
            # Get all taxa that share the same higher-level classifications
            name = current_taxon['scientific_name']
            rank = current_taxon['rank']
            
            # Build lineage by finding taxa with matching classifications
            if current_taxon.get('kingdom'):
                # Find kingdom
                self.cursor.execute("""
                    SELECT * FROM taxa 
                    WHERE rank = 'Kingdom' AND scientific_name = ?
                    LIMIT 1
                """, (current_taxon['kingdom'],))
                kingdom = self.cursor.fetchone()
                if kingdom and dict(kingdom)['id'] != current_taxon['id']:
                    lineage.insert(0, dict(kingdom))
                    
            if current_taxon.get('division'):
                # Find division
                self.cursor.execute("""
                    SELECT * FROM taxa 
                    WHERE rank IN ('Division', 'Phylum') AND scientific_name = ?
                    LIMIT 1
                """, (current_taxon['division'],))
                division = self.cursor.fetchone()
                if division and dict(division)['id'] != current_taxon['id']:
                    div_dict = dict(division)
                    if div_dict not in lineage:
                        lineage.insert(len([t for t in lineage if t.get('rank') == 'Kingdom']), div_dict)
                        
            if current_taxon.get('class') and rank != 'Class':
                self.cursor.execute("""
                    SELECT * FROM taxa 
                    WHERE rank = 'Class' AND scientific_name = ?
                    LIMIT 1
                """, (current_taxon['class'],))
                class_row = self.cursor.fetchone()
                if class_row and dict(class_row)['id'] != current_taxon['id']:
                    class_dict = dict(class_row)
                    if class_dict not in lineage:
                        insert_pos = len([t for t in lineage if t.get('rank') in ('Kingdom', 'Division', 'Phylum')])
                        lineage.insert(insert_pos, class_dict)
                        
            if current_taxon.get('order_name') and rank != 'Order':
                self.cursor.execute("""
                    SELECT * FROM taxa 
                    WHERE rank = 'Order' AND scientific_name = ?
                    LIMIT 1
                """, (current_taxon['order_name'],))
                order = self.cursor.fetchone()
                if order and dict(order)['id'] != current_taxon['id']:
                    order_dict = dict(order)
                    if order_dict not in lineage:
                        insert_pos = len([t for t in lineage if t.get('rank') in ('Kingdom', 'Division', 'Phylum', 'Class')])
                        lineage.insert(insert_pos, order_dict)
                        
            if current_taxon.get('family') and rank != 'Family':
                self.cursor.execute("""
                    SELECT * FROM taxa 
                    WHERE rank = 'Family' AND scientific_name = ?
                    LIMIT 1
                """, (current_taxon['family'],))
                family = self.cursor.fetchone()
                if family and dict(family)['id'] != current_taxon['id']:
                    family_dict = dict(family)
                    if family_dict not in lineage:
                        insert_pos = len([t for t in lineage if t.get('rank') in ('Kingdom', 'Division', 'Phylum', 'Class', 'Order')])
                        lineage.insert(insert_pos, family_dict)
                        
            if current_taxon.get('genus') and rank != 'Genus':
                self.cursor.execute("""
                    SELECT * FROM taxa 
                    WHERE rank = 'Genus' AND scientific_name = ?
                    LIMIT 1
                """, (current_taxon['genus'],))
                genus = self.cursor.fetchone()
                if genus and dict(genus)['id'] != current_taxon['id']:
                    genus_dict = dict(genus)
                    if genus_dict not in lineage:
                        insert_pos = len([t for t in lineage if t.get('rank') in ('Kingdom', 'Division', 'Phylum', 'Class', 'Order', 'Family')])
                        lineage.insert(insert_pos, genus_dict)
        else:
            # Use parent_tsn chain (for ITIS data)
            parent_tsn = current_taxon.get('parent_tsn')
            while parent_tsn:
                parent = self.get_taxon_by_tsn(parent_tsn)
                if not parent:
                    break
                lineage.insert(0, parent)
                parent_tsn = parent.get('parent_tsn')
            
        return lineage
        
    def get_children(self, tsn: int) -> List[Dict[str, Any]]:
        """Get all direct children of a taxon."""
        self.cursor.execute("""
            SELECT * FROM taxa WHERE parent_tsn = ?
            ORDER BY scientific_name
        """, (tsn,))
        
        return [dict(row) for row in self.cursor.fetchall()]
        
    def get_children_by_taxon_data(self, taxon_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get children of a taxon (works with both ITIS and GBIF data).
        
        Args:
            taxon_data: Taxon dictionary with rank and classification info
            
        Returns:
            List of child taxa
        """
        # For ITIS data with parent_tsn relationships
        if taxon_data.get('tsn'):
            return self.get_children(taxon_data['tsn'])
            
        # For GBIF data, find children based on hierarchical relationships
        rank = taxon_data['rank']
        name = taxon_data['scientific_name']
        
        # Determine child rank and matching field
        rank_hierarchy = {
            'Kingdom': ('division', 'Division', 'Phylum'),
            'Division': ('class', 'Class'),
            'Phylum': ('class', 'Class'),
            'Class': ('order_name', 'Order'),
            'Order': ('family', 'Family'),
            'Family': ('genus', 'Genus'),
            'Genus': ('species', 'Species'),
        }
        
        if rank not in rank_hierarchy:
            return []
            
        field, child_rank = rank_hierarchy[rank][:2]
        if len(rank_hierarchy[rank]) > 2:
            child_ranks = rank_hierarchy[rank][1:]
        else:
            child_ranks = (child_rank,)
        
        # Find children that have this taxon in their lineage
        placeholders = ','.join(['?' for _ in child_ranks])
        self.cursor.execute(f"""
            SELECT * FROM taxa 
            WHERE {field} = ? AND rank IN ({placeholders})
            ORDER BY scientific_name
        """, (name,) + child_ranks)
        
        return [dict(row) for row in self.cursor.fetchall()]
        
    def get_common_names(self, tsn: int) -> List[str]:
        """Get all common names for a taxon."""
        self.cursor.execute("""
            SELECT common_name FROM common_names WHERE tsn = ?
        """, (tsn,))
        
        return [row[0] for row in self.cursor.fetchall()]
        
    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics."""
        stats = {}
        
        # Total taxa
        self.cursor.execute("SELECT COUNT(*) FROM taxa")
        stats['total_taxa'] = self.cursor.fetchone()[0]
        
        # Count by rank
        self.cursor.execute("""
            SELECT rank, COUNT(*) as count 
            FROM taxa 
            GROUP BY rank 
            ORDER BY count DESC
        """)
        stats['by_rank'] = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        # Total common names
        self.cursor.execute("SELECT COUNT(*) FROM common_names")
        stats['total_common_names'] = self.cursor.fetchone()[0]
        
        return stats
