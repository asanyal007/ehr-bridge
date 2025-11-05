"""
Person ID Service for OMOP CDM
Generates stable person_id hashes and manages caching for patient identification.
"""
import hashlib
from typing import Dict, Optional, Tuple
import sqlite3
import os
from dataclasses import dataclass


@dataclass
class PersonKey:
    mrn: str = ""
    first_name: str = ""
    last_name: str = ""
    dob: str = ""  # YYYY-MM-DD format


class PersonIDService:
    """
    Service for generating and caching stable person_id hashes for OMOP PERSON table.
    """

    def __init__(self, db_path: str = "data/person_ids.db"):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        """Ensure SQLite database exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE person_ids (
                        id_hash TEXT PRIMARY KEY,
                        person_id INTEGER NOT NULL,
                        key_data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_seen TEXT NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX idx_person_key ON person_ids(key_data)")

    def generate_person_id(self, person_key: PersonKey) -> int:
        """
        Generate stable person_id hash from person key
        """
        # Normalize key data
        key_str = f"{person_key.mrn}|{person_key.first_name}|{person_key.last_name}|{person_key.dob}"
        key_str = key_str.lower().strip()

        # Check cache first
        cached = self._get_cached_person_id(key_str)
        if cached:
            self._update_last_seen(key_str)
            return cached

        # Generate new hash-based ID
        hash_obj = hashlib.sha256(key_str.encode('utf-8'))
        person_id = int(hash_obj.hexdigest()[:12], 16)

        # Store in cache
        self._store_person_id(key_str, person_id)
        return person_id

    def _get_cached_person_id(self, key_str: str) -> Optional[int]:
        """Get cached person_id for key"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT person_id FROM person_ids WHERE key_data = ?
            """, (key_str,))
            row = cursor.fetchone()
            return row[0] if row else None

    def _store_person_id(self, key_str: str, person_id: int):
        """Store person_id mapping"""
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO person_ids (id_hash, person_id, key_data, created_at, last_seen)
                VALUES (?, ?, ?, ?, ?)
            """, (hashlib.sha256(key_str.encode()).hexdigest(), person_id, key_str, now, now))

    def _update_last_seen(self, key_str: str):
        """Update last seen timestamp"""
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE person_ids SET last_seen = ? WHERE key_data = ?
            """, (now, key_str))


# Global service instance
_person_service: Optional[PersonIDService] = None

def get_person_id_service() -> PersonIDService:
    """Get or create person ID service singleton"""
    global _person_service
    if _person_service is None:
        _person_service = PersonIDService()
    return _person_service
