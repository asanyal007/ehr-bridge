"""
Visit ID Service for OMOP CDM
Generates stable visit_occurrence_id hashes and manages caching for visit identification.
"""
import hashlib
from typing import Dict, Optional, Tuple
import sqlite3
import os
from dataclasses import dataclass


@dataclass
class VisitKey:
    person_id: int
    visit_date: str = ""  # YYYY-MM-DD format
    visit_type: str = ""  # inpatient, outpatient, etc.
    facility: str = ""
    source_id: str = ""  # external visit identifier


class VisitIDService:
    """
    Service for generating and caching stable visit_occurrence_id hashes for OMOP VISIT_OCCURRENCE table.
    """

    def __init__(self, db_path: str = "data/visit_ids.db"):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        """Ensure SQLite database exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE visit_ids (
                        id_hash TEXT PRIMARY KEY,
                        visit_occurrence_id INTEGER NOT NULL,
                        key_data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_seen TEXT NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX idx_visit_key ON visit_ids(key_data)")

    def generate_visit_id(self, visit_key: VisitKey) -> int:
        """
        Generate stable visit_occurrence_id hash from visit key
        """
        # Normalize key data
        key_str = f"{visit_key.person_id}|{visit_key.visit_date}|{visit_key.visit_type}|{visit_key.facility}|{visit_key.source_id}"
        key_str = key_str.lower().strip()

        # Check cache first
        cached = self._get_cached_visit_id(key_str)
        if cached:
            self._update_last_seen(key_str)
            return cached

        # Generate new hash-based ID
        hash_obj = hashlib.sha256(key_str.encode('utf-8'))
        visit_id = int(hash_obj.hexdigest()[:12], 16)

        # Store in cache
        self._store_visit_id(key_str, visit_id)
        return visit_id

    def _get_cached_visit_id(self, key_str: str) -> Optional[int]:
        """Get cached visit_occurrence_id for key"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT visit_occurrence_id FROM visit_ids WHERE key_data = ?
            """, (key_str,))
            row = cursor.fetchone()
            return row[0] if row else None

    def _store_visit_id(self, key_str: str, visit_id: int):
        """Store visit_occurrence_id mapping"""
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO visit_ids (id_hash, visit_occurrence_id, key_data, created_at, last_seen)
                VALUES (?, ?, ?, ?, ?)
            """, (hashlib.sha256(key_str.encode()).hexdigest(), visit_id, key_str, now, now))

    def _update_last_seen(self, key_str: str):
        """Update last seen timestamp"""
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE visit_ids SET last_seen = ? WHERE key_data = ?
            """, (now, key_str))


# Global service instance
_visit_service: Optional[VisitIDService] = None

def get_visit_id_service() -> VisitIDService:
    """Get or create visit ID service singleton"""
    global _visit_service
    if _visit_service is None:
        _visit_service = VisitIDService()
    return _visit_service
