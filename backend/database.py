"""
SQLite Database Manager for AI Data Interoperability Platform
Handles all database operations for mapping jobs and user profiles
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from models import MappingJob, JobStatus, FieldMapping


class DatabaseManager:
    """Manager for SQLite database operations"""
    
    def __init__(self, db_path: str = "data/interop.db"):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database schema
        self._init_schema()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_schema(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Mappings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jobId TEXT UNIQUE NOT NULL,
                    appId TEXT NOT NULL DEFAULT 'default_app',
                    sourceSchema TEXT NOT NULL,
                    targetSchema TEXT NOT NULL,
                    suggestedMappings TEXT DEFAULT '[]',
                    finalMappings TEXT DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'DRAFT',
                    userId TEXT NOT NULL,
                    createdAt TEXT NOT NULL,
                    updatedAt TEXT NOT NULL
                )
            """)
            
            # User profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userId TEXT UNIQUE NOT NULL,
                    username TEXT,
                    email TEXT,
                    sessionToken TEXT,
                    createdAt TEXT NOT NULL,
                    lastLogin TEXT
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mappings_userId 
                ON mappings(userId)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mappings_appId 
                ON mappings(appId)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mappings_status 
                ON mappings(status)
            """)

            # Chat conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Chat messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    query_json TEXT,
                    results_count INTEGER,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES chat_conversations(conversation_id)
                )
            """)
            
            # Create indexes for chat tables
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation 
                ON chat_messages(conversation_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp 
                ON chat_messages(timestamp)
            """)

            # Terminology normalization table (approved mappings per field)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terminology_normalizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jobId TEXT NOT NULL,
                    fieldPath TEXT NOT NULL,
                    strategy TEXT DEFAULT 'hybrid',
                    system TEXT,
                    mapping_json TEXT NOT NULL DEFAULT '{}',
                    approvedBy TEXT,
                    createdAt TEXT NOT NULL,
                    updatedAt TEXT NOT NULL,
                    UNIQUE(jobId, fieldPath)
                )
            """)

            # Terminology cache table (fast lookups of prior decisions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terminology_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context TEXT NOT NULL, -- e.g., FHIR path or field label
                    sourceValue TEXT NOT NULL,
                    normalizedValue TEXT,
                    system TEXT,
                    code TEXT,
                    display TEXT,
                    hits INTEGER DEFAULT 1,
                    lastSeen TEXT NOT NULL,
                    UNIQUE(context, sourceValue)
                )
            """)

            # OMOP Concept Embeddings table (pre-computed S-BERT embeddings)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS concept_embeddings (
                    concept_id INTEGER PRIMARY KEY,
                    concept_name TEXT NOT NULL,
                    vocabulary_id TEXT NOT NULL,
                    domain_id TEXT NOT NULL,
                    embedding BLOB NOT NULL,  -- Serialized numpy array
                    standard_concept TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (concept_id) REFERENCES concept(concept_id)
                )
            """)

            # Concept Mapping Cache table (approved mappings from previous runs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS concept_mapping_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_system TEXT NOT NULL,
                    source_code TEXT NOT NULL,
                    source_display TEXT,
                    target_domain TEXT NOT NULL,
                    concept_id INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT,
                    approved_by TEXT,
                    approved_at TEXT NOT NULL,
                    hits INTEGER DEFAULT 1,
                    last_used TEXT NOT NULL,
                    UNIQUE(source_system, source_code, target_domain)
                )
            """)

            # Concept Review Queue table (HITL review items)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS concept_review_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    fhir_resource_id TEXT,
                    source_field TEXT NOT NULL,  -- e.g., "code.coding[0]"
                    source_code TEXT NOT NULL,
                    source_system TEXT NOT NULL,
                    source_display TEXT,
                    target_domain TEXT NOT NULL,
                    suggested_concept_id INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT,
                    alternatives TEXT,  -- JSON array of alternative concepts
                    status TEXT DEFAULT 'pending',  -- pending, approved, rejected
                    reviewed_by TEXT,
                    reviewed_at TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_concept_embeddings_vocab 
                ON concept_embeddings(vocabulary_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_concept_embeddings_domain 
                ON concept_embeddings(domain_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mapping_cache_lookup 
                ON concept_mapping_cache(source_system, source_code, target_domain)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_review_queue_job 
                ON concept_review_queue(job_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_review_queue_status 
                ON concept_review_queue(status)
            """)
    
    def create_job(self, job: MappingJob, app_id: str = "default_app") -> str:
        """
        Create a new mapping job
        
        Args:
            job: MappingJob object
            app_id: Application ID for multi-tenant support
            
        Returns:
            Created job ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.utcnow().isoformat()
            job_id = job.jobId if job.jobId else f"job_{int(datetime.utcnow().timestamp() * 1000)}"
            
            cursor.execute("""
                INSERT INTO mappings (
                    jobId, appId, sourceSchema, targetSchema,
                    suggestedMappings, finalMappings, status, userId,
                    createdAt, updatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                app_id,
                json.dumps(job.sourceSchema),
                json.dumps(job.targetSchema),
                json.dumps([m.model_dump() for m in job.suggestedMappings]),
                json.dumps([m.model_dump() for m in job.finalMappings]),
                job.status.value,
                job.userId,
                now,
                now
            ))
            
            return job_id
    
    def get_job(self, job_id: str) -> Optional[MappingJob]:
        """
        Retrieve a mapping job by ID
        
        Args:
            job_id: Job identifier
            
        Returns:
            MappingJob object or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM mappings WHERE jobId = ?
            """, (job_id,))
            
            row = cursor.fetchone()
            
            if row:
                return self._row_to_job(row)
            return None
    
    def get_all_jobs(self, user_id: Optional[str] = None, app_id: str = "default_app") -> List[MappingJob]:
        """
        Retrieve all mapping jobs, optionally filtered by user
        
        Args:
            user_id: Optional user ID filter
            app_id: Application ID
            
        Returns:
            List of MappingJob objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute("""
                    SELECT * FROM mappings 
                    WHERE appId = ? AND userId = ?
                    ORDER BY createdAt DESC
                """, (app_id, user_id))
            else:
                cursor.execute("""
                    SELECT * FROM mappings 
                    WHERE appId = ?
                    ORDER BY createdAt DESC
                """, (app_id,))
            
            rows = cursor.fetchall()
            return [self._row_to_job(row) for row in rows]
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a mapping job
        
        Args:
            job_id: Job identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Serialize JSON fields if present
            if 'suggestedMappings' in updates:
                updates['suggestedMappings'] = json.dumps(updates['suggestedMappings'])
            if 'finalMappings' in updates:
                updates['finalMappings'] = json.dumps(updates['finalMappings'])
            if 'sourceSchema' in updates:
                updates['sourceSchema'] = json.dumps(updates['sourceSchema'])
            if 'targetSchema' in updates:
                updates['targetSchema'] = json.dumps(updates['targetSchema'])
            
            # Always update timestamp
            updates['updatedAt'] = datetime.utcnow().isoformat()
            
            # Build dynamic UPDATE query
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [job_id]
            
            cursor.execute(f"""
                UPDATE mappings 
                SET {set_clause}
                WHERE jobId = ?
            """, values)
            
            return cursor.rowcount > 0

    # ---------------------------
    # Terminology normalization
    # ---------------------------

    def upsert_terminology_normalization(self, job_id: str, field_path: str, payload: Dict[str, Any]) -> bool:
        now = datetime.utcnow().isoformat()
        mapping_json = json.dumps(payload.get('mapping') or {})
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO terminology_normalizations (jobId, fieldPath, strategy, system, mapping_json, approvedBy, createdAt, updatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(jobId, fieldPath) DO UPDATE SET
                    strategy = excluded.strategy,
                    system = excluded.system,
                    mapping_json = excluded.mapping_json,
                    approvedBy = excluded.approvedBy,
                    updatedAt = excluded.updatedAt
                """,
                (
                    job_id,
                    field_path,
                    payload.get('strategy', 'hybrid'),
                    payload.get('system'),
                    mapping_json,
                    payload.get('approvedBy'),
                    now,
                    now,
                ),
            )
            return True

    def get_terminology_normalizations(self, job_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT jobId, fieldPath, strategy, system, mapping_json, approvedBy, createdAt, updatedAt
                FROM terminology_normalizations
                WHERE jobId = ?
                ORDER BY fieldPath
                """,
                (job_id,),
            )
            rows = cursor.fetchall()
            result = []
            for r in rows:
                item = dict(r)
                item['mapping'] = json.loads(item.pop('mapping_json') or '{}')
                result.append(item)
            return result

    def get_terminology_normalization(self, job_id: str, field_path: str) -> Optional[Dict[str, Any]]:
        """Get terminology normalization for a specific job and field path"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT jobId, fieldPath, strategy, system, mapping_json, approvedBy, createdAt, updatedAt
                FROM terminology_normalizations
                WHERE jobId = ? AND fieldPath = ?
                """,
                (job_id, field_path),
            )
            row = cursor.fetchone()
            if row:
                result = dict(row)
                # Parse the mapping_json
                if result.get('mapping_json'):
                    try:
                        result['mapping'] = json.loads(result['mapping_json'])
                    except json.JSONDecodeError:
                        result['mapping'] = {}
                return result
            return None

    def cache_normalization(self, context: str, source_value: str, normalized: Dict[str, Any]):
        now = datetime.utcnow().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO terminology_cache (context, sourceValue, normalizedValue, system, code, display, hits, lastSeen)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(context, sourceValue) DO UPDATE SET
                    normalizedValue = excluded.normalizedValue,
                    system = excluded.system,
                    code = excluded.code,
                    display = excluded.display,
                    hits = terminology_cache.hits + 1,
                    lastSeen = excluded.lastSeen
                """,
                (
                    context,
                    source_value,
                    normalized.get('normalized'),
                    normalized.get('system'),
                    normalized.get('code'),
                    normalized.get('display'),
                    now,
                ),
            )

    def get_cached_normalization(self, context: str, source_value: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT normalizedValue, system, code, display, hits, lastSeen
                FROM terminology_cache
                WHERE context = ? AND sourceValue = ?
                """,
                (context, source_value),
            )
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            return {
                'normalized': d.get('normalizedValue'),
                'system': d.get('system'),
                'code': d.get('code'),
                'display': d.get('display'),
                'hits': d.get('hits'),
                'lastSeen': d.get('lastSeen'),
            }
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a mapping job
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM mappings WHERE jobId = ?
            """, (job_id,))
            
            return cursor.rowcount > 0
    
    def create_or_update_user(self, user_id: str, username: str = None, email: str = None) -> bool:
        """
        Create or update user profile
        
        Args:
            user_id: User identifier
            username: Optional username
            email: Optional email
            
        Returns:
            True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            cursor.execute("""
                INSERT INTO user_profiles (userId, username, email, createdAt, lastLogin)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(userId) DO UPDATE SET
                    username = COALESCE(excluded.username, username),
                    email = COALESCE(excluded.email, email),
                    lastLogin = excluded.lastLogin
            """, (user_id, username, email, now, now))
            
            return True
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile dictionary or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM user_profiles WHERE userId = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def _row_to_job(self, row: sqlite3.Row) -> MappingJob:
        """Convert database row to MappingJob object"""
        return MappingJob(
            jobId=row['jobId'],
            sourceSchema=json.loads(row['sourceSchema']),
            targetSchema=json.loads(row['targetSchema']),
            suggestedMappings=[
                FieldMapping(**m) for m in json.loads(row['suggestedMappings'])
            ],
            finalMappings=[
                FieldMapping(**m) for m in json.loads(row['finalMappings'])
            ],
            status=JobStatus(row['status']),
            userId=row['userId'],
            createdAt=row['createdAt'],
            updatedAt=row['updatedAt']
        )
    
    # ========================================================================
    # Chat Methods
    # ========================================================================
    
    def save_chat_message(
        self, 
        conversation_id: str, 
        user_id: str,
        role: str, 
        content: str, 
        query_json: Optional[str] = None,
        results_count: Optional[int] = None
    ):
        """
        Save a chat message to the database
        
        Args:
            conversation_id: Unique conversation identifier
            user_id: User ID who owns the conversation
            role: 'user' or 'assistant'
            content: Message content
            query_json: Optional JSON string of the MongoDB query
            results_count: Optional count of results returned
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ensure conversation exists
            cursor.execute("""
                INSERT OR IGNORE INTO chat_conversations (conversation_id, user_id, created_at)
                VALUES (?, ?, ?)
            """, (conversation_id, user_id, datetime.utcnow().isoformat()))
            
            # Insert message
            cursor.execute("""
                INSERT INTO chat_messages 
                (conversation_id, role, content, query_json, results_count, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                conversation_id,
                role,
                content,
                query_json,
                results_count,
                datetime.utcnow().isoformat()
            ))
    
    def get_chat_history(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get chat history for a conversation
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to return (default: 50)
        
        Returns:
            List of message dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT role, content, query_json, results_count, timestamp
                FROM chat_messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """, (conversation_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def delete_conversation(self, conversation_id: str):
        """
        Delete a conversation and all its messages
        
        Args:
            conversation_id: Conversation ID to delete
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete messages
            cursor.execute("""
                DELETE FROM chat_messages WHERE conversation_id = ?
            """, (conversation_id,))
            
            # Delete conversation
            cursor.execute("""
                DELETE FROM chat_conversations WHERE conversation_id = ?
            """, (conversation_id,))
    
    def get_user_conversations(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get list of conversations for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations
        
        Returns:
            List of conversation dictionaries with metadata
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    c.conversation_id,
                    c.created_at,
                    COUNT(m.id) as message_count,
                    MAX(m.timestamp) as last_message_at
                FROM chat_conversations c
                LEFT JOIN chat_messages m ON c.conversation_id = m.conversation_id
                WHERE c.user_id = ?
                GROUP BY c.conversation_id
                ORDER BY last_message_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # ========================================================================
    # OMOP Concept Methods
    # ========================================================================
    
    def store_concept_embedding(
        self, 
        concept_id: int,
        concept_name: str,
        vocabulary_id: str,
        domain_id: str,
        embedding: bytes,
        standard_concept: str = None
    ):
        """
        Store a concept embedding in the database
        
        Args:
            concept_id: OMOP concept ID
            concept_name: Concept name
            vocabulary_id: Vocabulary ID (LOINC, SNOMED, etc.)
            domain_id: Domain ID (Condition, Measurement, etc.)
            embedding: Serialized numpy array as bytes
            standard_concept: Standard concept flag ('S' for standard)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO concept_embeddings 
                (concept_id, concept_name, vocabulary_id, domain_id, embedding, standard_concept, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                concept_id,
                concept_name,
                vocabulary_id,
                domain_id,
                embedding,
                standard_concept,
                datetime.utcnow().isoformat()
            ))
    
    def get_concept_embeddings(
        self, 
        vocabulary_id: str = None, 
        domain_id: str = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get concept embeddings with optional filters
        
        Args:
            vocabulary_id: Filter by vocabulary (LOINC, SNOMED, etc.)
            domain_id: Filter by domain (Condition, Measurement, etc.)
            limit: Maximum number of results
        
        Returns:
            List of concept embedding records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM concept_embeddings WHERE 1=1"
            params = []
            
            if vocabulary_id:
                query += " AND vocabulary_id = ?"
                params.append(vocabulary_id)
            
            if domain_id:
                query += " AND domain_id = ?"
                params.append(domain_id)
            
            query += " ORDER BY concept_id LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def cache_concept_mapping(
        self,
        source_system: str,
        source_code: str,
        source_display: str,
        target_domain: str,
        concept_id: int,
        confidence: float,
        reasoning: str = None,
        approved_by: str = None
    ):
        """
        Cache an approved concept mapping for future use
        
        Args:
            source_system: Source code system (http://loinc.org, etc.)
            source_code: Source code value
            source_display: Source display text
            target_domain: Target OMOP domain
            concept_id: Approved OMOP concept ID
            confidence: Confidence score
            reasoning: Reasoning for the mapping
            approved_by: User who approved the mapping
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.utcnow().isoformat()
            
            # Check if mapping already exists
            cursor.execute("""
                SELECT id, hits FROM concept_mapping_cache 
                WHERE source_system = ? AND source_code = ? AND target_domain = ?
            """, (source_system, source_code, target_domain))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing mapping
                cursor.execute("""
                    UPDATE concept_mapping_cache 
                    SET concept_id = ?, confidence = ?, reasoning = ?, 
                        approved_by = ?, approved_at = ?, hits = hits + 1, last_used = ?
                    WHERE id = ?
                """, (concept_id, confidence, reasoning, approved_by, now, now, existing[0]))
            else:
                # Insert new mapping
                cursor.execute("""
                    INSERT INTO concept_mapping_cache 
                    (source_system, source_code, source_display, target_domain, 
                     concept_id, confidence, reasoning, approved_by, approved_at, 
                     hits, last_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (source_system, source_code, source_display, target_domain,
                      concept_id, confidence, reasoning, approved_by, now, now))
    
    def get_cached_concept_mapping(
        self,
        source_system: str,
        source_code: str,
        target_domain: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a cached concept mapping
        
        Args:
            source_system: Source code system
            source_code: Source code value
            target_domain: Target OMOP domain
        
        Returns:
            Cached mapping or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM concept_mapping_cache 
                WHERE source_system = ? AND source_code = ? AND target_domain = ?
            """, (source_system, source_code, target_domain))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def add_to_review_queue(
        self,
        job_id: str,
        fhir_resource_id: str,
        source_field: str,
        source_code: str,
        source_system: str,
        source_display: str,
        target_domain: str,
        suggested_concept_id: int,
        confidence: float,
        reasoning: str,
        alternatives: str  # JSON string
    ) -> int:
        """
        Add a concept mapping to the review queue
        
        Args:
            job_id: Job ID
            fhir_resource_id: FHIR resource ID
            source_field: Source field path
            source_code: Source code
            source_system: Source system
            source_display: Source display text
            target_domain: Target domain
            suggested_concept_id: Suggested concept ID
            confidence: Confidence score
            reasoning: Reasoning text
            alternatives: JSON string of alternative concepts
        
        Returns:
            Review queue item ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO concept_review_queue 
                (job_id, fhir_resource_id, source_field, source_code, source_system, 
                 source_display, target_domain, suggested_concept_id, confidence, 
                 reasoning, alternatives, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job_id, fhir_resource_id, source_field, source_code, source_system,
                  source_display, target_domain, suggested_concept_id, confidence,
                  reasoning, alternatives, datetime.utcnow().isoformat()))
            
            return cursor.lastrowid
    
    def get_review_queue(
        self,
        job_id: str,
        status: str = 'pending',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get items from the review queue
        
        Args:
            job_id: Job ID
            status: Status filter (pending, approved, rejected)
            limit: Maximum number of results
        
        Returns:
            List of review queue items
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM concept_review_queue 
                WHERE job_id = ? AND status = ?
                ORDER BY created_at ASC
                LIMIT ?
            """, (job_id, status, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def approve_concept_mapping(
        self,
        review_id: int,
        selected_concept_id: int,
        reviewed_by: str
    ):
        """
        Approve a concept mapping from the review queue
        
        Args:
            review_id: Review queue item ID
            selected_concept_id: Selected concept ID
            reviewed_by: User who approved
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get the review item
            cursor.execute("""
                SELECT * FROM concept_review_queue WHERE id = ?
            """, (review_id,))
            
            review_item = cursor.fetchone()
            if not review_item:
                raise ValueError(f"Review item {review_id} not found")
            
            # Update status
            cursor.execute("""
                UPDATE concept_review_queue 
                SET status = 'approved', reviewed_by = ?, reviewed_at = ?
                WHERE id = ?
            """, (reviewed_by, datetime.utcnow().isoformat(), review_id))
            
            # Cache the approved mapping
            self.cache_concept_mapping(
                source_system=review_item[6],  # source_system
                source_code=review_item[5],   # source_code
                source_display=review_item[7], # source_display
                target_domain=review_item[8],  # target_domain
                concept_id=selected_concept_id,
                confidence=review_item[10],   # confidence
                reasoning=review_item[11],    # reasoning
                approved_by=reviewed_by
            )
    
    def reject_concept_mapping(
        self,
        review_id: int,
        reviewed_by: str
    ):
        """
        Reject a concept mapping from the review queue
        
        Args:
            review_id: Review queue item ID
            reviewed_by: User who rejected
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE concept_review_queue 
                SET status = 'rejected', reviewed_by = ?, reviewed_at = ?
                WHERE id = ?
            """, (reviewed_by, datetime.utcnow().isoformat(), review_id))


# Global database manager instance
db_manager = None

def get_db_manager(db_path: str = "data/interop.db") -> DatabaseManager:
    """Get or create database manager singleton"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager(db_path)
    return db_manager

