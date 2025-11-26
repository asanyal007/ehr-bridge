from __future__ import annotations

import asyncio
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import csv
from pymongo import MongoClient
from database import get_db_manager
from fhir_transformer import fhir_transformer
from fhir_resources import fhir_resources

from ingestion_models import (
    ConnectorType,
    JobMetrics,
)
from fhir_id_service import generate_fhir_id


@dataclass
class ConnectorConfig:
    connector_id: str
    connector_type: ConnectorType
    name: str
    config: Dict[str, Any]
    enabled: bool = True


@dataclass
class IngestionJobConfig:
    job_id: str
    job_name: str
    source_connector: ConnectorConfig
    destination_connector: ConnectorConfig
    mapping_job_id: Optional[str] = None
    resource_type_override: Optional[str] = None
    transformation_rules: List[Dict[str, Any]] = field(default_factory=list)
    schedule_config: Dict[str, Any] = field(default_factory=dict)
    error_handling: Dict[str, Any] = field(default_factory=dict)
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    # FHIR Store configuration
    fhir_store_enabled: bool = True
    fhir_store_db: str = "ehr"
    fhir_store_mode: str = "per_resource"  # per_resource | unified
    # OMOP Auto-Sync configuration
    omop_auto_sync: bool = True  # Automatically sync FHIR → OMOP
    omop_target_table: Optional[str] = None  # Auto-predict if None
    omop_sync_batch_size: int = 100  # Process in batches


class IngestionJob:
    def __init__(self, config: IngestionJobConfig):
        self.config = config
        self.metrics = JobMetrics()
        self.status = "CREATED"
        self._task: Optional[asyncio.Task] = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._stop = False
        # Error tracking
        self.error_message: Optional[str] = None
        self.error_details: Optional[Dict[str, Any]] = None
        # Optional CSV rows cache for demo sources
        self._rows: List[Dict[str, Any]] = []
        self._row_idx: int = 0
        # Optional Mongo destination client
        self._mongo_client: Optional[MongoClient] = None
        # FHIR store settings from config
        self._fhir_store_enabled: bool = config.fhir_store_enabled
        self._fhir_store_db: str = config.fhir_store_db
        # OMOP auto-sync settings from config
        self._omop_auto_sync: bool = config.omop_auto_sync
        self._omop_target_table: Optional[str] = config.omop_target_table
        self._omop_sync_count: int = 0  # Track synced OMOP records
        # Mapping job context
        self._job: Optional[Any] = None
        self._final_mappings: List[Any] = []
        self._resource_type: Optional[str] = None

    def _prepare_sources(self):
        # If CSV source configured, try to load rows
        try:
            if self.config.source_connector.connector_type == ConnectorType.csv_file:
                file_path = self.config.source_connector.config.get('file_path')
                if file_path:
                    import os
                    # Handle relative paths - try relative to project root
                    if not os.path.isabs(file_path):
                        # Try relative to backend directory
                        backend_dir = os.path.dirname(os.path.abspath(__file__))
                        project_root = os.path.dirname(backend_dir)
                        # Try multiple possible locations
                        possible_paths = [
                            file_path,  # Original path
                            os.path.join(backend_dir, file_path),  # Relative to backend
                            os.path.join(project_root, file_path),  # Relative to project root
                            os.path.join(project_root, 'data', file_path),  # In data folder
                            os.path.join(project_root, 'examples', file_path),  # In examples folder
                        ]
                        
                        found_path = None
                        for path in possible_paths:
                            if os.path.exists(path) and os.path.isfile(path):
                                found_path = path
                                break
                        
                        if found_path:
                            file_path = found_path
                        else:
                            print(f"[ERROR] Ingestion job {self.config.job_id}: CSV file not found. Tried: {possible_paths}")
                            self._rows = []
                            return
                    
                    if not os.path.exists(file_path):
                        print(f"[ERROR] Ingestion job {self.config.job_id}: CSV file does not exist: {file_path}")
                        self._rows = []
                        return
                    
                    with open(file_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        self._rows = list(reader)
                        print(f"[INFO] Ingestion job {self.config.job_id}: Loaded {len(self._rows)} rows from CSV: {file_path}")
                else:
                    print(f"[WARN] Ingestion job {self.config.job_id}: CSV source configured but no file_path provided")
                    self._rows = []
            else:
                print(f"[INFO] Ingestion job {self.config.job_id}: Source type {self.config.source_connector.connector_type.value}, no CSV rows loaded")
                self._rows = []
        except Exception as e:
            # Log source prep failures
            import traceback
            print(f"[ERROR] Ingestion job {self.config.job_id}: Failed to load source data: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            self._rows = []
        
        # If Mongo destination configured, init client
        try:
            if self.config.destination_connector.connector_type == ConnectorType.mongodb:
                uri = self.config.destination_connector.config.get('uri', 'mongodb://localhost:27017')
                db_name = self.config.destination_connector.config.get('database', 'ehr')
                coll_name = self.config.destination_connector.config.get('collection', 'staging')
                
                self._mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
                # Test connection
                self._mongo_client.admin.command('ping')
                # FHIR store uses the same Mongo (db configurable)
                self._fhir_store_db = db_name
                print(f"[INFO] Ingestion job {self.config.job_id}: MongoDB client initialized - uri={uri}, db={db_name}, collection={coll_name}")
            else:
                print(f"[WARN] Ingestion job {self.config.job_id}: Destination type {self.config.destination_connector.connector_type.value}, MongoDB client not initialized")
                self._mongo_client = None
        except Exception as e:
            print(f"[ERROR] Ingestion job {self.config.job_id}: Failed to initialize MongoDB client: {e}")
            self._mongo_client = None

        # Load mapping job context if available (same ID convention)
        try:
            db = get_db_manager()
            mapping_id = self.config.mapping_job_id or self.config.job_id
            job = db.get_job(mapping_id)
            if job:
                self._job = job
                # Prefer approved mappings; fallback to suggestions
                self._final_mappings = job.finalMappings if job.finalMappings else job.suggestedMappings
                # Infer FHIR resource type from mapping target paths
                self._resource_type = self.config.resource_type_override or self._infer_resource_type_from_mappings(self._final_mappings)
        except Exception:
            self._job = None
            self._final_mappings = []
            self._resource_type = None

    def _infer_resource_type_from_mappings(self, mappings: List[Any]) -> Optional[str]:
        try:
            available = set(fhir_resources.get_available_resources())
            for m in mappings:
                target = m.targetField if hasattr(m, 'targetField') else m.get('targetField')
                if not target or not isinstance(target, str):
                    continue
                # e.g., 'Patient.name[0].family' -> 'Patient'
                prefix = target.split('.', 1)[0]
                # strip array suffix if target starts without resource prefix
                if prefix in available:
                    return prefix
            # Fallback
            return None
        except Exception:
            return None

    async def start(self):
        if self.status in {"RUNNING", "PAUSED"}:
            return False
        
        # Prepare sources and validate configuration
        self._prepare_sources()
        
        # Validate configuration before starting
        has_source = bool(self._rows) if self.config.source_connector.connector_type == ConnectorType.csv_file else True
        has_destination = bool(self._mongo_client) if self.config.destination_connector.connector_type == ConnectorType.mongodb else True
        
        if not has_source:
            error_msg = f"Cannot start - no source data available. Source connector: {self.config.source_connector.connector_type.value}, Config: {self.config.source_connector.config}"
            print(f"[ERROR] Ingestion job {self.config.job_id}: {error_msg}")
            self.status = "ERROR"
            self.error_message = error_msg
            self.error_details = {
                "type": "source_missing",
                "source_connector": self.config.source_connector.connector_type.value,
                "source_config": self.config.source_connector.config,
                "rows_loaded": len(self._rows)
            }
            return False
        
        if not has_destination:
            error_msg = f"Cannot start - destination not configured. Destination connector: {self.config.destination_connector.connector_type.value}, Config: {self.config.destination_connector.config}"
            print(f"[ERROR] Ingestion job {self.config.job_id}: {error_msg}")
            self.status = "ERROR"
            self.error_message = error_msg
            self.error_details = {
                "type": "destination_missing",
                "destination_connector": self.config.destination_connector.connector_type.value,
                "destination_config": self.config.destination_connector.config,
                "mongo_client_initialized": self._mongo_client is not None
            }
            return False
        
        print(f"[INFO] Ingestion job {self.config.job_id}: Starting with {len(self._rows)} source rows, MongoDB destination ready")
        self.status = "RUNNING"
        self.metrics.start_time = datetime.now()
        self._stop = False
        self._task = asyncio.create_task(self._run_loop())
        return True

    async def stop(self):
        if self.status not in {"RUNNING", "PAUSED"}:
            return False
        self._stop = True
        self._pause_event.set()
        if self._task:
            await asyncio.sleep(0)  # yield
        self.status = "STOPPED"
        return True

    async def pause(self):
        if self.status != "RUNNING":
            return False
        self.status = "PAUSED"
        self._pause_event.clear()
        return True

    async def resume(self):
        if self.status != "PAUSED":
            return False
        self.status = "RUNNING"
        self._pause_event.set()
        return True

    def _write_to_mongo(self, record: Dict[str, Any]) -> bool:
        """
        Write record to MongoDB destination
        
        Returns:
            True if successful, False otherwise
        """
        if not self._mongo_client:
            print(f"[WARN] Ingestion job {self.config.job_id}: MongoDB client not initialized")
            return False
        try:
            db_name = self.config.destination_connector.config.get('database', 'ehr')
            coll_name = self.config.destination_connector.config.get('collection', 'staging')
            db = self._mongo_client[db_name]
            coll = db[coll_name]
            doc = dict(record)
            doc['job_id'] = self.config.job_id
            doc['ingested_at'] = datetime.utcnow()
            coll.insert_one(doc)
            return True
        except Exception as e:
            # Log error but don't crash the loop
            print(f"[ERROR] Ingestion job {self.config.job_id}: Failed to write to MongoDB: {e}")
            return False

    def _upsert_fhir_store(self, resource: Optional[Dict[str, Any]]):
        if not self._fhir_store_enabled or not self._mongo_client or not resource or not isinstance(resource, dict):
            return
        try:
            resource_type = str(resource.get('resourceType') or '').strip() or None
            if not resource_type:
                return
            # Ensure deterministic id
            resource = dict(resource)
            rid = generate_fhir_id(resource)
            resource['id'] = rid
            meta = dict(resource.get('meta') or {})
            meta['lastUpdated'] = datetime.utcnow().isoformat()
            resource['meta'] = meta

            db = self._mongo_client[self._fhir_store_db]
            coll = db[f"fhir_{resource_type}"]
            # Indexes (best effort, ignore errors if exist)
            try:
                coll.create_index('id', unique=True)
                coll.create_index([('job_id', 1), ('persisted_at', -1)])
            except Exception:
                pass

            resource_doc = dict(resource)
            resource_doc['job_id'] = self.config.job_id
            resource_doc['persisted_at'] = datetime.utcnow()

            from pymongo import UpdateOne
            result = coll.bulk_write([
                UpdateOne({'id': rid}, {'$set': resource_doc}, upsert=True)
            ], ordered=True)
            
            # Log upsert result for debugging
            if result.upserted_count > 0:
                print(f"[INFO] Ingestion job {self.config.job_id}: Inserted new FHIR {resource_type} record (id: {rid})")
            elif result.modified_count > 0:
                print(f"[INFO] Ingestion job {self.config.job_id}: Updated existing FHIR {resource_type} record (id: {rid})")
            
            # Auto-sync to OMOP if enabled
            if self._omop_auto_sync:
                self._sync_fhir_to_omop(resource_doc)
        except Exception as e:
            # Log error instead of silently swallowing
            print(f"[ERROR] Ingestion job {self.config.job_id}: FHIR store upsert failed: {e}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            # Still non-fatal for ingestion loop, but now we know about errors
    
    def _sync_fhir_to_omop(self, fhir_resource: Dict[str, Any]):
        """
        Automatically sync a FHIR resource to OMOP collections.
        Called immediately after FHIR store upsert if omop_auto_sync is enabled.
        """
        if not self._mongo_client:
            return
        
        try:
            from omop_engine import transform_fhir_to_omop
            
            # Determine OMOP table if not specified
            target_table = self._omop_target_table
            if not target_table:
                # Auto-predict based on FHIR resource type
                resource_type = fhir_resource.get('resourceType', '')
                if resource_type == 'Patient':
                    target_table = 'PERSON'
                elif resource_type == 'Observation':
                    target_table = 'MEASUREMENT'
                elif resource_type == 'Condition':
                    target_table = 'CONDITION_OCCURRENCE'
                elif resource_type == 'MedicationRequest':
                    target_table = 'DRUG_EXPOSURE'
                else:
                    # Skip unknown resource types
                    return
            
            # Transform FHIR → OMOP
            omop_rows = transform_fhir_to_omop(fhir_resource, target_table)
            
            if not omop_rows:
                return
            
            # Persist to OMOP collections
            db = self._mongo_client[self._fhir_store_db]
            now = datetime.utcnow()
            
            for row in omop_rows:
                table_name = row.get('_table', target_table)
                coll = db[f"omop_{table_name}"]
                
                # Enrich with metadata
                doc = dict(row)
                doc.pop('_table', None)  # Remove internal key
                doc['job_id'] = self.config.job_id
                doc['persisted_at'] = now
                doc['synced_from_fhir'] = True
                
                # Upsert based on person_id or a composite key
                person_id = doc.get('person_id')
                if person_id:
                    from pymongo import UpdateOne
                    coll.bulk_write([
                        UpdateOne({'person_id': person_id, 'job_id': self.config.job_id}, 
                                {'$set': doc}, upsert=True)
                    ], ordered=False)
                else:
                    # Insert without upsert for non-person tables
                    coll.insert_one(doc)
                
                self._omop_sync_count += 1
        except Exception as e:
            # Log but don't fail ingestion
            print(f"OMOP auto-sync error: {e}")
            pass

    def _write_failed_to_mongo(self, record: Optional[Dict[str, Any]] = None, reason: str = "transformation_failed"):
        if not self._mongo_client:
            return
        try:
            db_name = self.config.destination_connector.config.get('database', 'ehr')
            base_coll = self.config.destination_connector.config.get('collection', 'staging')
            dlq_coll = f"{base_coll}_dlq"
            db = self._mongo_client[db_name]
            coll = db[dlq_coll]
            doc = dict(record) if isinstance(record, dict) else {}
            doc['job_id'] = self.config.job_id
            doc['failed_at'] = datetime.utcnow()
            doc['error_reason'] = reason
            coll.insert_one(doc)
        except Exception:
            pass

    async def _run_loop(self):
        # Simulate streaming: every 200ms receive a record, process it
        try:
            while not self._stop:
                await self._pause_event.wait()
                await asyncio.sleep(0.2)
                self.metrics.received += 1
                
                # Check if we have data source and destination configured
                has_source_data = bool(self._rows)
                has_destination = bool(self._mongo_client)
                
                if not has_source_data:
                    print(f"[WARN] Ingestion job {self.config.job_id}: No source data available (CSV rows: {len(self._rows)})")
                    # Still increment received but don't process
                    self.metrics.last_update = datetime.now()
                    continue
                
                if not has_destination:
                    print(f"[WARN] Ingestion job {self.config.job_id}: MongoDB destination not configured")
                    # Still increment received but don't process
                    self.metrics.last_update = datetime.now()
                    continue
                
                # Simulate transformation success ~95% of time
                if self.metrics.received % 20 == 0:
                    self.metrics.failed += 1
                    # On simulated failure, write a failed record to DLQ if possible
                    failed_sample = None
                    if self._rows:
                        failed_sample = self._rows[(self._row_idx) % len(self._rows)]
                    self._write_failed_to_mongo(failed_sample, reason="simulated_failure")
                else:
                    # Process record: transform to FHIR (if mappings exist) then write
                    record = self._rows[self._row_idx % len(self._rows)]
                    self._row_idx += 1
                    out_doc: Dict[str, Any] = dict(record)
                    write_success = False
                    
                    try:
                        if self._final_mappings and (self._resource_type or True):
                            # Ensure mappings are plain dicts for transformer
                            mapped = []
                            for m in self._final_mappings:
                                if hasattr(m, 'model_dump'):
                                    mapped.append(m.model_dump())
                                elif isinstance(m, dict):
                                    mapped.append(m)
                            resource_type = self._resource_type or 'Patient'
                            fhir_doc = fhir_transformer.columnar_to_fhir(record, mapped, resource_type)
                            out_doc = fhir_doc
                            # Also upsert into FHIR store
                            self._upsert_fhir_store(fhir_doc)
                    except Exception as e:
                        # On transform error, send to DLQ and continue
                        print(f"[ERROR] Ingestion job {self.config.job_id}: Transform error: {e}")
                        self.metrics.failed += 1
                        self._write_failed_to_mongo(record, reason=f"transform_error: {str(e)}")
                        out_doc = None
                    
                    if out_doc is not None:
                        write_success = self._write_to_mongo(out_doc)
                        if write_success:
                            # Only increment processed if write was successful
                            self.metrics.processed += 1
                        else:
                            # Write failed, count as failed
                            self.metrics.failed += 1
                            self._write_failed_to_mongo(record, reason="mongodb_write_failed")
                
                self.metrics.last_update = datetime.now()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            import traceback
            error_msg = f"Fatal error in run loop: {str(e)}"
            print(f"[ERROR] Ingestion job {self.config.job_id}: {error_msg}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            self.status = "ERROR"
            self.error_message = error_msg
            self.error_details = {
                "type": "runtime_error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            raise


class IngestionEngine:
    def __init__(self):
        self.jobs: Dict[str, IngestionJob] = {}

    def create_job(self, config: IngestionJobConfig) -> str:
        self.jobs[config.job_id] = IngestionJob(config)
        return config.job_id

    async def start_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            return False
        return await job.start()

    async def stop_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            return False
        return await job.stop()

    def list_jobs(self) -> List[Dict[str, Any]]:
        return [self._job_status_dict(jid) for jid in self.jobs]

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        return self._job_status_dict(job_id)

    def get_engine_stats(self) -> Dict[str, Any]:
        total_received = sum(j.metrics.received for j in self.jobs.values())
        total_processed = sum(j.metrics.processed for j in self.jobs.values())
        total_failed = sum(j.metrics.failed for j in self.jobs.values())
        running_jobs = len([j for j in self.jobs.values() if j.status in {"RUNNING", "PAUSED"}])
        return {
            "total_jobs": len(self.jobs),
            "running_jobs": running_jobs,
            "total_received": total_received,
            "total_processed": total_processed,
            "total_failed": total_failed,
        }

    def _job_status_dict(self, job_id: str) -> Dict[str, Any]:
        job = self.jobs[job_id]
        status_dict = {
            "job_id": job_id,
            "job_name": job.config.job_name,
            "status": job.status,
            "mapping_job_id": job.config.mapping_job_id,
            "resource_type": job.config.resource_type_override,
            "source_connector": {
                "connector_id": job.config.source_connector.connector_id,
                "connector_type": job.config.source_connector.connector_type.value,
                "name": job.config.source_connector.name,
                "config": job.config.source_connector.config,
                "enabled": job.config.source_connector.enabled,
            },
            "destination_connector": {
                "connector_id": job.config.destination_connector.connector_id,
                "connector_type": job.config.destination_connector.connector_type.value,
                "name": job.config.destination_connector.name,
                "config": job.config.destination_connector.config,
                "enabled": job.config.destination_connector.enabled,
            },
            "metrics": job.metrics.to_dict(),
        }
        
        # Include error information if status is ERROR
        if job.status == "ERROR":
            status_dict["error"] = {
                "message": job.error_message or "Unknown error occurred",
                "details": job.error_details or {}
            }
        
        return status_dict


_engine: Optional[IngestionEngine] = None


def get_ingestion_engine() -> IngestionEngine:
    global _engine
    if _engine is None:
        _engine = IngestionEngine()
    return _engine
