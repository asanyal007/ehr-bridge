"""
FastAPI Backend for AI Data Interoperability Platform
Healthcare/EHR/HL7 focused with Sentence-BERT semantic matching
SQLite database, JWT authentication, containerized deployment
"""
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Depends, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import (
    MappingJob, 
    JobStatus, 
    CreateJobRequest, 
    AnalyzeJobRequest,
    ApproveJobRequest,
    TransformRequest,
    FieldMapping,
    TransformationType
)
from database import get_db_manager
from auth import (
    create_access_token,
    create_demo_token,
    get_current_user,
    optional_auth,
    TokenData
)
from bio_ai_engine import get_bio_ai_engine
from mongodb_client import get_mongo_client
from hl7_transformer import hl7_transformer
from csv_handler import csv_handler
from fhir_resources import fhir_resources
from fhir_transformer import fhir_transformer
from gemini_ai import get_gemini_ai
from hl7_parser_advanced import get_hl7_advanced_parser
from routing_engine import get_routing_engine
from visual_mapper import get_visual_mapper
from ingestion_engine import get_ingestion_engine, IngestionJobConfig, ConnectorConfig
from ingestion_models import (
    CreateIngestionJobRequest, JobControlRequest, ConnectorConfigResponse,
    JobStatusResponse, JobListResponse, EngineStatsResponse, CONNECTOR_TEMPLATES,
)
from omop_engine import predict_table_from_schema, preview_omop, persist_omop, persist_all_omop
from omop_vocab import get_vocab_service
from fastapi import Body  # ensure Body is imported
from fhir_id_service import generate_fhir_id


# Initialize FastAPI app
app = FastAPI(
    title="AI Data Interoperability Platform API",
    description="Healthcare/EHR/HL7 Data Mapping with Sentence-BERT",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get database manager
db = get_db_manager()

# Get MongoDB client for HL7 staging
mongo = get_mongo_client()

# AI engine will be loaded on first use (lazy loading)
ai_engine = None


def get_ai_engine():
    """Lazy load AI engine"""
    global ai_engine
    if ai_engine is None:
        ai_engine = get_bio_ai_engine()
    return ai_engine


# Request/Response Models
class LoginRequest(BaseModel):
    """Mock login request"""
    userId: str
    username: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response with JWT token"""
    token: str
    userId: str
    username: str


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("[START] Starting AI Data Interoperability Platform")
    print("[INFO] Initializing SQLite database...")
    # Database is already initialized in get_db_manager()
    print("[OK] Database ready")


# Root endpoint removed - now serves frontend via catch-all route at the end


@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Mock login endpoint - creates JWT token
    In production, verify credentials against database
    
    Args:
        request: Login credentials
        
    Returns:
        JWT token and user info
    """
    # Create or update user in database
    db.create_or_update_user(request.userId, username=request.username)
    
    # Generate JWT token
    token = create_access_token(request.userId, username=request.username)
    
    return LoginResponse(
        token=token,
        userId=request.userId,
        username=request.username or request.userId
    )


@app.post("/api/v1/auth/demo-token", response_model=LoginResponse)
async def get_demo_token():
    """
    Generate a demo token for testing
    
    Returns:
        Demo JWT token and user info
    """
    user_id = f"demo_user_{int(datetime.utcnow().timestamp())}"
    username = f"Demo User"
    
    # Create user in database
    db.create_or_update_user(user_id, username=username)
    
    # Generate token
    token = create_demo_token(user_id)
    
    return LoginResponse(
        token=token,
        userId=user_id,
        username=username
    )


@app.get("/api/v1/jobs", response_model=List[MappingJob])
async def get_jobs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Retrieve all mapping jobs from SQLite database
    
    Args:
        user_id: Optional user ID to filter jobs
        current_user: Current authenticated user (optional)
        
    Returns:
        List of mapping jobs
    """
    try:
        # Development mode: return all jobs regardless of user filter
        jobs = db.get_all_jobs()
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving jobs: {str(e)}")


@app.get("/api/v1/jobs/{job_id}", response_model=MappingJob)
async def get_job(
    job_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Retrieve a specific mapping job by ID
    
    Args:
        job_id: Job identifier
        current_user: Current authenticated user
        
    Returns:
        Mapping job details
    """
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Check authorization
    if current_user and job.userId != current_user.userId:
        # In production, check if user has read permission
        pass
    
    return job


@app.post("/api/v1/jobs", response_model=MappingJob)
async def create_job(
    request: CreateJobRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create a new mapping job in SQLite (status: DRAFT)
    
    Args:
        request: Job creation request with schemas
        current_user: Current authenticated user
        
    Returns:
        Created mapping job
    """
    try:
        # Verify user owns this request
        # Permissive: if anonymous, set userId to anon
        if current_user.userId == 'anon':
            request.userId = 'anon'
        
        # Create new job object
        job = MappingJob(
            jobId="",  # Will be auto-generated
            sourceSchema=request.sourceSchema,
            targetSchema=request.targetSchema,
            suggestedMappings=[],
            finalMappings=[],
            status=JobStatus.DRAFT,
            userId=request.userId
        )
        
        # Save to database
        job_id = db.create_job(job)
        
        # Retrieve and return the created job
        created_job = db.get_job(job_id)
        return created_job
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")


@app.put("/api/v1/jobs/{job_id}/schemas")
async def update_job_schemas(
    job_id: str,
    request: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update job schemas and trigger re-analysis

    Args:
        job_id: Job identifier
        request: Updated schemas
        current_user: Authenticated user

    Returns:
        Updated job
    """
    try:
        # Get existing job
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Update schemas
        source_schema = request.get('sourceSchema')
        target_schema = request.get('targetSchema')

        if not source_schema or not target_schema:
            raise HTTPException(status_code=400, detail="Both sourceSchema and targetSchema are required")

        # Update job in database
        db.update_job(job_id, {
            'sourceSchema': source_schema,
            'targetSchema': target_schema,
            'status': JobStatus.DRAFT.value
        })

        # Trigger re-analysis
        await analyze_job(job_id, AnalyzeJobRequest(userId=current_user.userId or 'anon'), current_user)

        # Return updated job
        return db.get_job(job_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update job schemas: {str(e)}")


# ============================================================================
# TERMINOLOGY NORMALIZATION ENDPOINTS
# ============================================================================
from models import (
    TerminologyNormalizeRequest, TerminologyNormalizeResponse,
    TerminologySuggestion, TerminologyCandidate, TerminologyNormalization
)


@app.post("/api/v1/terminology/normalize/{job_id}", response_model=TerminologyNormalizeResponse)
async def generate_terminology_suggestions(
    job_id: str,
    request: TerminologyNormalizeRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Analyze sample data and suggest terminology normalization for fields mapped
    to FHIR code-like elements and enumerations. Uses hybrid: cache → S-BERT → Gemini.
    """
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    # derive candidate fields from finalMappings if present, else suggested
    mappings = job.finalMappings or job.suggestedMappings or []
    # collect distinct values per source field from request.sampleData (optional)
    distincts: Dict[str, Dict[str, int]] = {}
    samples = request.sampleData or []
    # Fallback: try to read CSV staging for this job if no samples provided
    if (not samples) and mongo.is_connected():
        try:
            staged = mongo.get_messages_by_job(job_id, limit=1)
            for msg in staged:
                if msg.get('message_type') == 'CSV_FILE' and msg.get('raw_message'):
                    parsed = csv_handler.csv_to_json(msg['raw_message'])
                    if isinstance(parsed, list) and parsed:
                        samples = parsed[: max(1, min(request.sampleSize, 500))]
                        break
        except Exception:
            pass
    for row in samples[: request.sampleSize]:
        if not isinstance(row, dict):
            continue
        for m in mappings:
            src = m.sourceField if hasattr(m, 'sourceField') else m.get('sourceField')
            if not src:
                continue
            if src in row and row[src] is not None:
                val = str(row[src]).strip()
                if not val:
                    continue
                distincts.setdefault(src, {})[val] = distincts.setdefault(src, {}).get(val, 0) + 1

    # helpers
    bio = get_ai_engine()
    gemini = get_gemini_ai()
    from database import get_db_manager
    # Build suggestions
    suggestions: List[TerminologySuggestion] = []
    for m in mappings:
        src = m.sourceField if hasattr(m, 'sourceField') else m.get('sourceField')
        tgt = m.targetField if hasattr(m, 'targetField') else m.get('targetField')
        if not src or not tgt:
            continue
        # heuristic: only consider if target looks like FHIR code/enum fields
        lower_tgt = (tgt or "").lower()
        likely_code_like = any(k in lower_tgt for k in ["code", "coding", "codeableconcept", "gender", "marital", "status"])
        if not likely_code_like:
            continue
        values_counts = distincts.get(src, {})
        # If we have no sample-derived values, synthesize a small candidate set for common enums
        if not values_counts:
            if "gender" in lower_tgt:
                values_counts = {"M": 1, "F": 1, "male": 1, "female": 1}
            elif any(k in lower_tgt for k in ["status"]):
                values_counts = {"active": 1, "inactive": 1}
            else:
                values_counts = {}
            if values_counts:
                distincts[src] = values_counts
        values_sorted = sorted(values_counts.items(), key=lambda x: -x[1])
        sample_values = [v for v, _ in values_sorted[:50]]

        # Try cache first (context = target field path)
        candidates: List[TerminologyCandidate] = []
        for v in sample_values:
            cached = db.get_cached_normalization(tgt, v)
            if cached:
                candidates.append(TerminologyCandidate(
                    sourceValue=v,
                    normalized=cached.get('normalized') or v,
                    confidence=0.95,
                    source='cache',
                    system=cached.get('system'),
                    code=cached.get('code'),
                    display=cached.get('display')
                ))

        # For remaining values, use S-BERT for simple domains
        remaining = [v for v in sample_values if all(c.sourceValue != v for c in candidates)]
        for v in remaining:
            domain = "admin-gender" if "gender" in lower_tgt else ("boolean" if any(x in lower_tgt for x in ["flag", "bool"]) else "")
            if domain:
                res = bio.normalize_by_similarity(v, domain=domain)
                candidates.append(TerminologyCandidate(
                    sourceValue=v,
                    normalized=res.get('normalized', v),
                    confidence=float(res.get('confidence', 0.8)),
                    source='ai'
                ))

        # Use Gemini for code system & code suggestions (complex)
        gem_system = gemini.suggest_code_system(sample_values)
        gem_entries = gemini.suggest_code_entries(sample_values)
        # merge Gemini entries
        for ge in gem_entries:
            sv = str(ge.get('sourceValue'))
            # update or append
            found = next((c for c in candidates if c.sourceValue == sv), None)
            if found:
                if ge.get('normalized'):
                    found.normalized = ge['normalized']
                found.system = ge.get('system') or found.system
                found.code = ge.get('code') or found.code
                found.display = ge.get('display') or found.display
                found.confidence = max(found.confidence, float(ge.get('confidence', 0.8)))
            else:
                candidates.append(TerminologyCandidate(
                    sourceValue=sv,
                    normalized=str(ge.get('normalized') or sv),
                    confidence=float(ge.get('confidence', 0.8)),
                    source='ai',
                    system=ge.get('system'),
                    code=ge.get('code'),
                    display=ge.get('display')
                ))

        # Build suggestion object
        sug = TerminologySuggestion(
            fieldPath=tgt,
            suggestedSystem=gem_system.get('system'),
            strategy='hybrid',
            sourceDistincts=[{"value": v, "count": c} for v, c in values_sorted],
            candidates=candidates,
        )
        suggestions.append(sug)

    return TerminologyNormalizeResponse(jobId=job_id, suggestions=suggestions)


@app.get("/api/v1/terminology/{job_id}")
async def get_terminology(job_id: str, current_user: TokenData = Depends(get_current_user)):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"jobId": job_id, "normalizations": db.get_terminology_normalizations(job_id)}


@app.put("/api/v1/terminology/{job_id}")
async def save_terminology(job_id: str, payload: Dict[str, Any], current_user: TokenData = Depends(get_current_user)):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    # payload: { items: [{fieldPath, strategy, system?, mapping, approvedBy?}], cacheAlso?: true }
    items = payload.get('items') or []
    for item in items:
        field_path = item.get('fieldPath')
        if not field_path:
            continue
        db.upsert_terminology_normalization(job_id, field_path, item)
        # optionally cache entries for faster lookups
        if payload.get('cacheAlso') and isinstance(item.get('mapping'), dict):
            for sv, norm in item['mapping'].items():
                db.cache_normalization(field_path, sv, norm)
    return {"success": True, "updated": len(items)}


@app.post("/api/v1/jobs/{job_id}/analyze", response_model=MappingJob)
async def analyze_job(
    job_id: str,
    request: AnalyzeJobRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Trigger Sentence-BERT analysis and update job to PENDING_REVIEW
    
    Args:
        job_id: Job identifier
        request: Analysis request with user ID
        current_user: Current authenticated user
        
    Returns:
        Updated mapping job with AI suggestions
    """
    # Get the job
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Verify user owns the job
    # Permissive: allow anonymous or mismatched users during development
    
    try:
        # Update status to ANALYZING
        db.update_job(job_id, {"status": JobStatus.ANALYZING.value})
        
        # Run AI analysis using Sentence-BERT
        print(f"🧠 Analyzing schemas for job {job_id}...")
        engine = get_ai_engine()
        suggested_mappings = engine.analyze_schemas(
            job.sourceSchema,
            job.targetSchema
        )
        
        # Save suggested mappings and update status
        db.update_job(job_id, {
            "suggestedMappings": [m.model_dump() for m in suggested_mappings],
            "status": JobStatus.PENDING_REVIEW.value
        })
        
        # Retrieve and return updated job
        updated_job = db.get_job(job_id)
        return updated_job
    except Exception as e:
        # Update status to ERROR on failure
        db.update_job(job_id, {"status": JobStatus.ERROR.value})
        raise HTTPException(status_code=500, detail=f"Error analyzing schemas: {str(e)}")


@app.put("/api/v1/jobs/{job_id}/approve", response_model=MappingJob)
async def approve_job(
    job_id: str,
    request: ApproveJobRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update job with final mappings and set status to APPROVED
    
    Args:
        job_id: Job identifier
        request: Approval request with final mappings
        current_user: Current authenticated user
        
    Returns:
        Approved mapping job
    """
    # Get the job
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Verify user owns the job
    # Permissive
    
    try:
        # Approve the job with final mappings
        db.update_job(job_id, {
            "finalMappings": [m.model_dump() for m in request.finalMappings],
            "status": JobStatus.APPROVED.value
        })
        
        # Retrieve and return updated job
        updated_job = db.get_job(job_id)
        return updated_job
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving job: {str(e)}")


@app.delete("/api/v1/jobs/{job_id}")
async def delete_job(
    job_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Delete a mapping job
    
    Args:
        job_id: Job identifier
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # Get the job
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Verify user owns the job
    # Permissive
    
    try:
        db.delete_job(job_id)
        return {"message": f"Job {job_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")


@app.post("/api/v1/jobs/{job_id}/transform")
async def transform_data(
    job_id: str,
    request: TransformRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Execute transformation logic on sample data
    
    Args:
        job_id: Job identifier
        request: Transform request with mappings and sample data
        current_user: Current authenticated user
        
    Returns:
        Transformed data results
    """
    try:
        transformed_data = []
        
        for source_row in request.sampleData:
            target_row = {}
            
            for mapping in request.mappings:
                # Apply transformation based on type
                if mapping.suggestedTransform == TransformationType.DIRECT:
                    # Direct mapping
                    if mapping.sourceField in source_row:
                        target_row[mapping.targetField] = source_row[mapping.sourceField]
                
                elif mapping.suggestedTransform == TransformationType.CONCAT:
                    # Concatenate multiple fields
                    if mapping.transformParams and 'fields' in mapping.transformParams:
                        fields = mapping.transformParams['fields']
                        separator = mapping.transformParams.get('separator', ' ')
                        values = [str(source_row.get(f, '')) for f in fields if f in source_row]
                        target_row[mapping.targetField] = separator.join(values)
                
                elif mapping.suggestedTransform == TransformationType.SPLIT:
                    # Split a field
                    if mapping.sourceField in source_row:
                        separator = mapping.transformParams.get('separator', ' ') if mapping.transformParams else ' '
                        parts = str(source_row[mapping.sourceField]).split(separator)
                        index = mapping.transformParams.get('index', 0) if mapping.transformParams else 0
                        target_row[mapping.targetField] = parts[index] if index < len(parts) else ""
                
                elif mapping.suggestedTransform == TransformationType.UPPERCASE:
                    if mapping.sourceField in source_row:
                        target_row[mapping.targetField] = str(source_row[mapping.sourceField]).upper()
                
                elif mapping.suggestedTransform == TransformationType.LOWERCASE:
                    if mapping.sourceField in source_row:
                        target_row[mapping.targetField] = str(source_row[mapping.sourceField]).lower()
                
                elif mapping.suggestedTransform == TransformationType.TRIM:
                    if mapping.sourceField in source_row:
                        target_row[mapping.targetField] = str(source_row[mapping.sourceField]).strip()
                
                elif mapping.suggestedTransform == TransformationType.FORMAT_DATE:
                    # Simplified date formatting
                    if mapping.sourceField in source_row:
                        target_row[mapping.targetField] = source_row[mapping.sourceField]
                
                else:  # CUSTOM or unknown
                    if mapping.sourceField in source_row:
                        target_row[mapping.targetField] = source_row[mapping.sourceField]
            
            transformed_data.append(target_row)
        
        return {
            "jobId": job_id,
            "sourceData": request.sampleData,
            "transformedData": transformed_data,
            "recordCount": len(transformed_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transforming data: {str(e)}")


@app.get("/api/v1/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    try:
        # Test database connection
        jobs_count = len(db.get_all_jobs())
        db_status = f"connected ({jobs_count} jobs)"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check if AI engine is loaded
    ai_status = "loaded" if ai_engine is not None else "not loaded (lazy)"
    
    # Check MongoDB status
    mongo_stats = mongo.get_staging_stats() if mongo.is_connected() else {"connected": False}
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "mongodb": mongo_stats,
        "ai_engine": ai_status,
        "model": get_ai_engine().model_name if ai_engine else "sentence-transformers/all-MiniLM-L6-v2"
    }
# ============================================================================
# OMOP MODELING ENDPOINTS (PoC)
# ============================================================================

@app.post("/api/v1/omop/predict-table")
async def omop_predict_table(schema: Dict[str, str] = Body(...), job_id: str = Body(None)):
    """
    Predict OMOP table from schema.
    If job_id provided, will check actual data for FHIR resourceType.
    """
    # If job_id provided, check MongoDB for actual FHIR data
    if job_id:
        try:
            mongo = get_mongo_client()
            db = mongo.client['ehr']
            
            # Check staging collection first
            sample = db['staging'].find_one({'job_id': job_id})
            
            # If no staging data, check FHIR collections
            if not sample:
                for resource_type in ['Patient', 'Condition', 'Observation', 'DiagnosticReport', 'MedicationRequest']:
                    sample = db[f'fhir_{resource_type}'].find_one({'job_id': job_id})
                    if sample:
                        break
            
            # If we found FHIR data, use resourceType for direct mapping
            if sample and isinstance(sample, dict) and 'resourceType' in sample:
                resource_type = sample.get('resourceType')
                
                fhir_to_omop = {
                    'Patient': 'PERSON',
                    'Condition': 'CONDITION_OCCURRENCE',
                    'Observation': 'MEASUREMENT',
                    'DiagnosticReport': 'MEASUREMENT',
                    'MedicationRequest': 'DRUG_EXPOSURE',
                    'Procedure': 'PROCEDURE_OCCURRENCE',
                    'Encounter': 'VISIT_OCCURRENCE'
                }
                
                omop_table = fhir_to_omop.get(resource_type, 'PERSON')
                
                return {
                    "table": omop_table,
                    "confidence": 0.98,
                    "rationale": f"Direct mapping from FHIR {resource_type} resource (found in job data)",
                    "alternatives": [
                        {"table": omop_table, "confidence": 0.98, "rationale": f"FHIR {resource_type} → {omop_table}", "score": 10}
                    ]
                }
        except Exception as e:
            print(f"⚠️  Could not check job data: {e}")
            # Fall through to schema-based prediction
    
    # Fallback to schema-based prediction
    return predict_table_from_schema(schema)


@app.post("/api/v1/omop/preview")
async def omop_preview(job_id: str = Body(...), table: str = Body(None), limit: int = Body(20)):
    return preview_omop(job_id, table, limit)


@app.post("/api/v1/omop/persist")
async def omop_persist(job_id: str = Body(...), table: str = Body(...), rows: List[Dict[str, Any]] = Body(...)):
    return persist_omop(job_id, table, rows)


@app.post("/api/v1/omop/persist-all")
async def omop_persist_all(job_id: str = Body(...), table: str = Body(None)):
    return persist_all_omop(job_id, table)


# ----------------------------------------------------------------------------
# OMOP VIEWER ENDPOINTS (list tables, fetch data)
# ----------------------------------------------------------------------------
@app.get("/api/v1/omop/tables")
async def list_omop_tables(current_user: TokenData = Depends(get_current_user)):
    """List available OMOP tables (Mongo collections prefixed with omop_)."""
    try:
        from pymongo import MongoClient
        # Try to infer Mongo connection from any ingestion job, else use defaults
        uri = "mongodb://localhost:27017"
        db_name = "ehr"
        try:
            engine = get_ingestion_engine()
            jobs = engine.list_jobs()
            for j in jobs:
                dest = (j or {}).get('destination_connector', {})
                if (dest or {}).get('connector_type') == 'mongodb':
                    cfg = dest.get('config', {})
                    uri = cfg.get('uri', uri)
                    db_name = cfg.get('database', db_name)
                    break
        except Exception:
            pass

        client = MongoClient(uri)
        dbh = client[db_name]
        names = dbh.list_collection_names()
        tables = sorted([n.split('omop_', 1)[1] for n in names if n.startswith('omop_')])
        return {"success": True, "tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list OMOP tables: {str(e)}")


@app.get("/api/v1/omop/data")
async def get_omop_data(
    table: str = Query(..., description="OMOP table name (e.g., PERSON)"),
    job_id: Optional[str] = Query(None, description="Optional job_id filter"),
    limit: int = Query(100, le=1000),
    current_user: TokenData = Depends(get_current_user)
):
    """Fetch persisted OMOP rows from MongoDB, optionally filtered by job_id."""
    try:
        from pymongo import MongoClient
        from datetime import datetime as _dt
        uri = "mongodb://localhost:27017"
        db_name = "ehr"
        try:
            engine = get_ingestion_engine()
            jobs = engine.list_jobs()
            for j in jobs:
                dest = (j or {}).get('destination_connector', {})
                if (dest or {}).get('connector_type') == 'mongodb':
                    cfg = dest.get('config', {})
                    uri = cfg.get('uri', uri)
                    db_name = cfg.get('database', db_name)
                    break
        except Exception:
            pass

        client = MongoClient(uri)
        dbh = client[db_name]
        coll = dbh[f"omop_{table}"]
        query = {"job_id": job_id} if job_id else {}
        docs = list(coll.find(query).sort("persisted_at", -1).limit(int(limit)))

        def ser(d):
            d = dict(d)
            d.pop('_id', None)
            ts = d.get('persisted_at')
            if hasattr(ts, 'isoformat'):
                d['persisted_at'] = ts.isoformat()
            return d

        return {"success": True, "table": table, "count": len(docs), "rows": [ser(x) for x in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch OMOP data: {str(e)}")


@app.get("/api/v1/omop/stats")
async def get_omop_stats(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get OMOP collection statistics: total record counts per table.
    Useful for dashboard display and data validation.
    """
    try:
        from pymongo import MongoClient
        uri = "mongodb://localhost:27017"
        db_name = "ehr"
        try:
            engine = get_ingestion_engine()
            jobs = engine.list_jobs()
            for j in jobs:
                dest = (j or {}).get('destination_connector', {})
                if (dest or {}).get('connector_type') == 'mongodb':
                    cfg = dest.get('config', {})
                    uri = cfg.get('uri', uri)
                    db_name = cfg.get('database', db_name)
                    break
        except Exception:
            pass

        client = MongoClient(uri)
        dbh = client[db_name]
        names = dbh.list_collection_names()
        omop_collections = [n for n in names if n.startswith('omop_')]
        
        stats = {}
        total_records = 0
        for coll_name in omop_collections:
            table_name = coll_name.split('omop_', 1)[1]
            count = dbh[coll_name].count_documents({})
            stats[table_name] = count
            total_records += count
        
        return {
            "success": True,
            "total_records": total_records,
            "tables": stats,
            "table_count": len(stats)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch OMOP stats: {str(e)}")


@app.get("/api/v1/omop/compatible-jobs")
async def get_omop_compatible_jobs(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get list of job IDs that are compatible with OMOP persistence.
    A job is OMOP-compatible if it has:
    - CSV data in staging collection, OR
    - Supported FHIR resources (Patient, Observation, Condition, MedicationRequest, DiagnosticReport)
    
    Returns:
        {
            "compatible_jobs": [
                {
                    "job_id": "test_enhanced_measurements",
                    "source_type": "csv",
                    "record_count": 10,
                    "resource_types": ["staging"],
                    "omop_ready": true
                },
                ...
            ]
        }
    """
    try:
        from pymongo import MongoClient
        uri = "mongodb://localhost:27017"
        db_name = "ehr"
        
        try:
            engine = get_ingestion_engine()
            jobs = engine.list_jobs()
            for j in jobs:
                dest = (j or {}).get('destination_connector', {})
                if (dest or {}).get('connector_type') == 'mongodb':
                    cfg = dest.get('config', {})
                    uri = cfg.get('uri', uri)
                    db_name = cfg.get('database', db_name)
                    break
        except Exception:
            pass

        client = MongoClient(uri)
        dbh = client[db_name]
        
        # Supported FHIR resource types for OMOP mapping
        supported_fhir_types = ['Patient', 'Observation', 'Condition', 'MedicationRequest', 'DiagnosticReport']
        
        compatible_jobs = []
        
        # Get all unique job_ids from staging and FHIR collections
        all_job_ids = set()
        
        # Check staging
        for doc in dbh['staging'].find({'job_id': {'$exists': True}}).limit(1000):
            all_job_ids.add(doc.get('job_id'))
        
        # Check FHIR collections
        for resource_type in supported_fhir_types:
            coll_name = f'fhir_{resource_type}'
            if coll_name in dbh.list_collection_names():
                for doc in dbh[coll_name].find({'job_id': {'$exists': True}}).limit(1000):
                    all_job_ids.add(doc.get('job_id'))
        
        # For each job, determine compatibility
        for job_id in sorted(all_job_ids):
            job_info = {
                "job_id": job_id,
                "source_type": "unknown",
                "record_count": 0,
                "resource_types": [],
                "omop_ready": False
            }
            
            # Check staging collection
            staging_count = dbh['staging'].count_documents({'job_id': job_id})
            if staging_count > 0:
                # Check if it's CSV or FHIR in staging
                sample = dbh['staging'].find_one({'job_id': job_id})
                if sample and not sample.get('resourceType'):
                    # CSV-like data
                    job_info['source_type'] = 'csv'
                    job_info['record_count'] = staging_count
                    job_info['resource_types'].append('staging (CSV)')
                    job_info['omop_ready'] = True
                elif sample and sample.get('resourceType') in supported_fhir_types:
                    # FHIR data in staging
                    job_info['source_type'] = 'fhir'
                    job_info['record_count'] = staging_count
                    job_info['resource_types'].append(f"staging ({sample.get('resourceType')})")
                    job_info['omop_ready'] = True
            
            # Check FHIR collections
            for resource_type in supported_fhir_types:
                coll_name = f'fhir_{resource_type}'
                if coll_name in dbh.list_collection_names():
                    fhir_count = dbh[coll_name].count_documents({'job_id': job_id})
                    if fhir_count > 0:
                        job_info['source_type'] = 'fhir'
                        job_info['record_count'] += fhir_count
                        job_info['resource_types'].append(f'{resource_type} ({fhir_count})')
                        job_info['omop_ready'] = True
            
            # Only include compatible jobs
            if job_info['omop_ready']:
                compatible_jobs.append(job_info)
        
        return {
            "success": True,
            "compatible_jobs": compatible_jobs,
            "total_compatible": len(compatible_jobs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch OMOP-compatible jobs: {str(e)}")


# ----------------------------------------------------------------------------
# FHIR STORE VIEWER ENDPOINTS
# ----------------------------------------------------------------------------
@app.get("/api/v1/fhir/store/resources")
async def fhir_store_resources(current_user: TokenData = Depends(optional_auth)):
    try:
        from pymongo import MongoClient
        uri = "mongodb://localhost:27017"; db_name = "ehr"
        try:
            engine = get_ingestion_engine()
            for j in engine.list_jobs():
                dest = (j or {}).get('destination_connector', {})
                if (dest or {}).get('connector_type') == 'mongodb':
                    cfg = dest.get('config', {})
                    uri = cfg.get('uri', uri)
                    db_name = cfg.get('database', db_name)
                    break
        except Exception:
            pass
        client = MongoClient(uri)
        names = client[db_name].list_collection_names()
        types = sorted([n.split('fhir_', 1)[1] for n in names if n.startswith('fhir_')])
        return {"success": True, "resources": types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list FHIR resources: {str(e)}")


@app.get("/api/v1/fhir/store/{resource_type}")
async def fhir_store_query(
    resource_type: str,
    job_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: TokenData = Depends(optional_auth)
):
    try:
        from pymongo import MongoClient
        from pymongo import ASCENDING, DESCENDING
        uri = "mongodb://localhost:27017"; db_name = "ehr"
        try:
            engine = get_ingestion_engine()
            for j in engine.list_jobs():
                dest = (j or {}).get('destination_connector', {})
                if (dest or {}).get('connector_type') == 'mongodb':
                    cfg = dest.get('config', {})
                    uri = cfg.get('uri', uri)
                    db_name = cfg.get('database', db_name)
                    break
        except Exception:
            pass
        client = MongoClient(uri)
        coll = client[db_name][f"fhir_{resource_type}"]
        query: Dict[str, Any] = {}
        if job_id:
            query['job_id'] = job_id
        if q:
            query['$or'] = [
                {'id': {'$regex': q, '$options': 'i'}},
                {'name.family': {'$regex': q, '$options': 'i'}},
                {'name.given': {'$regex': q, '$options': 'i'}},
                {'identifier.value': {'$regex': q, '$options': 'i'}},
            ]
        docs = list(coll.find(query).sort('persisted_at', -1).limit(int(limit)))
        def ser(d):
            d = dict(d); d.pop('_id', None)
            if 'persisted_at' in d and hasattr(d['persisted_at'], 'isoformat'):
                d['persisted_at'] = d['persisted_at'].isoformat()
            return d
        return {"success": True, "resourceType": resource_type, "count": len(docs), "entries": [ser(x) for x in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query FHIR store: {str(e)}")


@app.get("/api/v1/fhir/store/{resource_type}/{rid}")
async def fhir_store_read(resource_type: str, rid: str, current_user: TokenData = Depends(optional_auth)):
    try:
        from pymongo import MongoClient
        uri = "mongodb://localhost:27017"; db_name = "ehr"
        client = MongoClient(uri)
        coll = client[db_name][f"fhir_{resource_type}"]
        doc = coll.find_one({'id': rid})
        if not doc:
            raise HTTPException(status_code=404, detail="Resource not found")
        doc.pop('_id', None)
        if 'persisted_at' in doc and hasattr(doc['persisted_at'], 'isoformat'):
            doc['persisted_at'] = doc['persisted_at'].isoformat()
        return {"success": True, "resource": doc}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read resource: {str(e)}")


# ============================================================================
# OMOP CONCEPT NORMALIZATION APIs
# ============================================================================

@app.get("/api/v1/omop/concepts/search")
async def search_concepts(
    query: Optional[str] = Query(None, description="Search term for concept name or code"),
    domain: Optional[str] = Query(None, description="OMOP domain (Condition, Measurement, Drug, etc.)"),
    vocabulary: Optional[str] = Query(None, description="Vocabulary ID (ICD10CM, LOINC, RxNorm, etc.)"),
    standard_only: bool = Query(False, description="Only standard concepts"),
    limit: int = Query(50, description="Maximum results", le=100)
):
    """Search OMOP concepts with filters"""
    try:
        vocab = get_vocab_service()
        concepts = vocab.search_concepts(
            query=query,
            domain=domain,
            vocabulary=vocabulary,
            standard_only=standard_only,
            limit=limit
        )
        return {
            "success": True,
            "concepts": [
                {
                    "concept_id": c.concept_id,
                    "concept_name": c.concept_name,
                    "domain_id": c.domain_id,
                    "vocabulary_id": c.vocabulary_id,
                    "concept_code": c.concept_code,
                    "standard_concept": c.standard_concept
                }
                for c in concepts
            ],
            "count": len(concepts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Concept search failed: {str(e)}")


@app.post("/api/v1/omop/concepts/normalize")
async def normalize_values(
    values: List[str] = Body(None, description="List of values to normalize (optional if job_id provided)"),
    domain: str = Body(..., description="OMOP domain"),
    vocabulary: Optional[str] = Body(None, description="Vocabulary filter"),
    job_id: Optional[str] = Body(None, description="Job ID to fetch real data from"),
    target_table: Optional[str] = Body(None, description="Target OMOP table to infer source fields")
):
    """
    Suggest concept mappings for values.
    If job_id is provided, automatically extracts real values from MongoDB data.
    """
    try:
        # Initialize extracted_values before any conditional blocks
        extracted_values = []
        
        # If job_id provided, fetch real data from MongoDB
        if job_id and not values:
            mongo = get_mongo_client()
            db_mongo = mongo.client['ehr']
            
            # Determine which fields to extract based on domain/target_table
            source_fields = []
            if domain == 'Condition' or target_table == 'CONDITION_OCCURRENCE':
                source_fields = ['diagnosis_code', 'condition_code', 'icd10', 'icd_code', 'primary_diagnosis_icd10']
            elif domain == 'Measurement' or target_table == 'MEASUREMENT':
                source_fields = ['loinc', 'lab_code', 'test_code', 'observation_code']
            elif domain == 'Drug' or target_table == 'DRUG_EXPOSURE':
                source_fields = ['drug_code', 'medication_code', 'rxnorm', 'ndc']
            
            # PRIORITY 1: Try FHIR collections FIRST (most likely source)
            fhir_collections = {
                'Condition': 'fhir_Condition',
                'Measurement': 'fhir_Observation',
                'Drug': 'fhir_MedicationRequest'
            }
            
            fhir_coll_name = fhir_collections.get(domain)
            if fhir_coll_name and fhir_coll_name in db_mongo.list_collection_names():
                try:
                    # Try with job_id first
                    records = list(db_mongo[fhir_coll_name].find({'job_id': job_id}).limit(20))
                    
                    # If no records with job_id, try without job_id filter (get any available data)
                    if not records:
                        print(f"⚠️  No records found for job_id={job_id} in {fhir_coll_name}, trying latest available data...")
                        records = list(db_mongo[fhir_coll_name].find({}).sort('_id', -1).limit(20))
                    
                    for record in records:
                        code_obj = record.get('code', {})
                        coding_list = code_obj.get('coding', [])
                        for coding in coding_list:
                            code = coding.get('code')
                            if code and code not in extracted_values:
                                extracted_values.append(str(code))
                    
                    extracted_values = extracted_values[:15]
                    if extracted_values:
                        print(f"✅ Extracted {len(extracted_values)} codes from {fhir_coll_name}")
                except Exception as e:
                    print(f"⚠️  Could not extract values from FHIR collection: {e}")
            
            # PRIORITY 2: Try staging collection if FHIR didn't work
            if not extracted_values:
                try:
                    records = list(db_mongo['staging'].find({'job_id': job_id}).limit(20))
                    
                    for record in records:
                        # If it's a FHIR resource, extract from code.coding array
                        if 'resourceType' in record:
                            resource_type = record.get('resourceType')
                            
                            if resource_type == 'Condition' and domain == 'Condition':
                                code_obj = record.get('code', {})
                                coding_list = code_obj.get('coding', [])
                                for coding in coding_list:
                                    code = coding.get('code')
                                    if code and code not in extracted_values:
                                        extracted_values.append(str(code))
                            
                            elif resource_type == 'Observation' and domain == 'Measurement':
                                code_obj = record.get('code', {})
                                coding_list = code_obj.get('coding', [])
                                for coding in coding_list:
                                    code = coding.get('code')
                                    if code and code not in extracted_values:
                                        extracted_values.append(str(code))
                        
                        # If it's CSV data, extract from specified fields
                        else:
                            for field in source_fields:
                                val = record.get(field)
                                if val and str(val) not in extracted_values:
                                    extracted_values.append(str(val))
                    
                    extracted_values = extracted_values[:15]
                    if extracted_values:
                        print(f"✅ Extracted {len(extracted_values)} values from staging collection")
                    
                except Exception as e:
                    print(f"⚠️  Could not extract values from staging: {e}")
            
            # Set values or return error
            if extracted_values:
                values = extracted_values
                print(f"✅ Using {len(values)} real values for concept normalization")
            else:
                # NO SYNTHETIC DATA! Return empty if no real data found
                values = []
                print(f"❌ No data found for job {job_id}, domain {domain}. No concepts to map.")
        
        # Check if we have any values to normalize
        if not values or len(values) == 0:
            return {
                "success": False,
                "message": f"No concepts to map. No data found for domain '{domain}' in job '{job_id}'.",
                "suggestions": [],
                "count": 0,
                "source": "none"
            }
        
        # Normalize values using vocabulary service
        vocab = get_vocab_service()
        suggestions = vocab.normalize_values(values or [], domain, vocabulary)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "count": len(suggestions),
            "source": "real_data" if job_id and extracted_values else "provided_values",
            "values_found": len(values)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Value normalization failed: {str(e)}")


@app.put("/api/v1/omop/concepts/approve")
async def approve_concept_mappings(
    job_id: str = Body(...),
    field_path: str = Body(...),
    mapping: Dict[str, Dict[str, Any]] = Body(...),
    approved_by: str = Body(...)
):
    """Approve concept mappings for a field"""
    try:
        db = get_db_manager()
        # Update terminology normalization table
        db.upsert_terminology_normalization(job_id, field_path, {
            "strategy": "omop_vocab",
            "mapping": mapping,
            "approvedBy": approved_by
        })
        return {"success": True, "updated": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")


# ============================================================================
# ENHANCED OMOP CONCEPT VALIDATION & REVIEW ENDPOINTS
# ============================================================================

@app.post("/api/v1/omop/concepts/validate")
async def validate_concept_mappings(
    job_id: str = Body(..., description="Job ID to validate"),
    auto_approve_threshold: float = Body(0.90, description="Threshold for auto-approval"),
    current_user: TokenData = Depends(optional_auth)
):
    """
    Analyze all concept mappings for a job
    Auto-approve high-confidence, queue low-confidence for review
    
    Returns:
    {
      "auto_approved": 150,
      "review_required": 12,
      "rejected": 3,
      "review_queue": [...]
    }
    """
    try:
        from omop_vocab import get_semantic_matcher
        
        matcher = get_semantic_matcher()
        results = matcher.validate_concept_mappings(job_id, auto_approve_threshold)
        
        return {
            "success": True,
            "job_id": job_id,
            "auto_approved": results.get("auto_approved", 0),
            "review_required": results.get("review_required", 0),
            "rejected": results.get("rejected", 0),
            "review_queue": results.get("review_queue", []),
            "threshold": auto_approve_threshold
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Concept validation failed: {str(e)}")


@app.get("/api/v1/omop/concepts/review-queue/{job_id}")
async def get_review_queue(
    job_id: str,
    status: str = Query('pending', description="Status filter (pending, approved, rejected)"),
    current_user: TokenData = Depends(optional_auth)
):
    """
    Get concepts requiring human review
    
    Returns list of pending concept mappings with:
    - Source information
    - Top 3 suggested concepts with confidence
    - Context from FHIR resource
    """
    try:
        db = get_db_manager()
        review_items = db.get_review_queue(job_id, status)
        
        return {
            "success": True,
            "job_id": job_id,
            "status": status,
            "items": review_items,
            "count": len(review_items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get review queue: {str(e)}")


@app.post("/api/v1/omop/concepts/approve-mapping")
async def approve_concept_mapping(
    review_id: int = Body(..., description="Review queue item ID"),
    selected_concept_id: int = Body(..., description="Selected concept ID"),
    current_user: TokenData = Depends(optional_auth)
):
    """
    User approves/overrides a concept mapping
    Updates cache for future use
    """
    try:
        db = get_db_manager()
        user_id = current_user.user_id if current_user else "anonymous"
        
        db.approve_concept_mapping(review_id, selected_concept_id, user_id)
        
        return {
            "success": True,
            "review_id": review_id,
            "concept_id": selected_concept_id,
            "approved_by": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve mapping: {str(e)}")


@app.post("/api/v1/omop/concepts/reject-mapping")
async def reject_concept_mapping(
    review_id: int = Body(..., description="Review queue item ID"),
    current_user: TokenData = Depends(optional_auth)
):
    """
    User rejects a concept mapping
    """
    try:
        db = get_db_manager()
        user_id = current_user.user_id if current_user else "anonymous"
        
        db.reject_concept_mapping(review_id, user_id)
        
        return {
            "success": True,
            "review_id": review_id,
            "rejected_by": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject mapping: {str(e)}")


@app.post("/api/v1/omop/concepts/bulk-approve")
async def bulk_approve_concepts(
    job_id: str = Body(..., description="Job ID"),
    approvals: List[Dict[str, Any]] = Body(..., description="List of {review_id, concept_id} pairs"),
    current_user: TokenData = Depends(optional_auth)
):
    """
    Approve multiple concept mappings at once
    """
    try:
        db = get_db_manager()
        user_id = current_user.user_id if current_user else "anonymous"
        
        approved_count = 0
        errors = []
        
        for approval in approvals:
            try:
                review_id = approval.get('review_id')
                concept_id = approval.get('concept_id')
                
                if not review_id or not concept_id:
                    errors.append(f"Invalid approval: {approval}")
                    continue
                
                db.approve_concept_mapping(review_id, concept_id, user_id)
                approved_count += 1
                
            except Exception as e:
                errors.append(f"Error approving {approval}: {str(e)}")
        
        return {
            "success": True,
            "job_id": job_id,
            "approved_count": approved_count,
            "total_requested": len(approvals),
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk approval failed: {str(e)}")


@app.get("/api/v1/omop/concepts/stats/{job_id}")
async def get_concept_stats(
    job_id: str,
    current_user: TokenData = Depends(optional_auth)
):
    """
    Get concept mapping statistics for a job
    """
    try:
        db = get_db_manager()
        
        # Get counts by status
        pending = db.get_review_queue(job_id, 'pending')
        approved = db.get_review_queue(job_id, 'approved')
        rejected = db.get_review_queue(job_id, 'rejected')
        
        return {
            "success": True,
            "job_id": job_id,
            "stats": {
                "pending": len(pending),
                "approved": len(approved),
                "rejected": len(rejected),
                "total": len(pending) + len(approved) + len(rejected)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get concept stats: {str(e)}")


# ============================================================================
# HL7 MESSAGE INGESTION & STAGING ENDPOINTS
# ============================================================================

class HL7IngestRequest(BaseModel):
    """Request model for HL7 message ingestion"""
    jobId: str
    messageId: str
    rawMessage: str
    messageType: str = "HL7_V2"
    metadata: Optional[Dict[str, Any]] = None


@app.post("/api/v1/hl7/ingest")
async def ingest_hl7_message(
    request: HL7IngestRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Ingest and stage an HL7 v2 message in MongoDB
    
    Args:
        request: HL7 ingestion request
        current_user: Authenticated user
        
    Returns:
        Staging confirmation with message ID
    """
    if not mongo.is_connected():
        raise HTTPException(status_code=503, detail="MongoDB not available for HL7 staging")
    
    try:
        # Stage message in MongoDB
        mongo_id = mongo.stage_hl7_message(
            message_id=request.messageId,
            job_id=request.jobId,
            raw_message=request.rawMessage,
            message_type=request.messageType,
            metadata=request.metadata
        )
        
        # Parse HL7 for preview
        parsed = mongo.parse_hl7_message(request.rawMessage)
        
        return {
            "success": True,
            "messageId": request.messageId,
            "mongoId": mongo_id,
            "jobId": request.jobId,
            "segmentCount": parsed.get('segment_count', 0),
            "segments": list(parsed.get('segments', {}).keys()),
            "ingestionTimestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting HL7 message: {str(e)}")


@app.get("/api/v1/hl7/messages/{job_id}")
async def get_staged_messages(
    job_id: str,
    limit: int = Query(100, le=1000),
    current_user: TokenData = Depends(optional_auth)
):
    """
    Get all staged HL7 messages for a job
    
    Args:
        job_id: Job identifier
        limit: Maximum messages to return
        current_user: Optional authenticated user
        
    Returns:
        List of staged messages
    """
    if not mongo.is_connected():
        raise HTTPException(status_code=503, detail="MongoDB not available")
    
    try:
        messages = mongo.get_messages_by_job(job_id, limit=limit)
        return {
            "jobId": job_id,
            "messageCount": len(messages),
            "messages": messages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")


@app.post("/api/v1/hl7/transform")
async def transform_hl7(
    request: TransformRequest,
    current_user: TokenData = Depends(optional_auth)
):
    """
    Transform HL7 v2 message to columnar format
    
    Args:
        request: Transform request with HL7 message
        current_user: Optional authenticated user
        
    Returns:
        Transformed columnar data
    """
    try:
        transformed_data = []
        
        for source_row in request.sampleData:
            # Check if source is HL7 (string) or already columnar (dict)
            if isinstance(source_row, str):
                # HL7 → Columnar transformation
                columnar = hl7_transformer.hl7_to_columnar(
                    source_row,
                    request.mappings
                )
                transformed_data.append(columnar)
            elif isinstance(source_row, dict):
                # Columnar → HL7 transformation
                hl7_message = hl7_transformer.columnar_to_hl7(
                    source_row,
                    request.mappings
                )
                transformed_data.append({"hl7_message": hl7_message})
        
        return {
            "success": True,
            "recordCount": len(transformed_data),
            "sourceData": request.sampleData,
            "transformedData": transformed_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transforming HL7: {str(e)}")


# ============================================================================
# CSV FILE UPLOAD & SCHEMA INFERENCE ENDPOINTS
# ============================================================================

@app.post("/api/v1/csv/infer-schema")
async def infer_csv_schema(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Infer schema from uploaded CSV file
    
    Args:
        file: Uploaded CSV file
        current_user: Authenticated user
        
    Returns:
        Inferred schema with column names and types
    """
    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Infer schema
        schema = csv_handler.infer_schema_from_csv(csv_content)
        
        # Also convert to JSON for preview
        data_preview = csv_handler.csv_to_json(csv_content)
        
        return {
            "success": True,
            "filename": file.filename,
            "schema": schema,
            "columnCount": len(schema),
            "rowCount": len(data_preview),
            "preview": data_preview[:5]  # First 5 rows
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inferring CSV schema: {str(e)}")


@app.post("/api/v1/csv/upload")
async def upload_csv_file(
    job_id: str,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Upload CSV file and associate with job
    
    Args:
        job_id: Job identifier
        file: Uploaded CSV file
        current_user: Authenticated user
        
    Returns:
        Upload confirmation with file info
    """
    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Store in MongoDB as staging (similar to HL7)
        if mongo.is_connected():
            message_id = f"CSV_{file.filename}_{int(datetime.utcnow().timestamp())}"
            mongo.stage_hl7_message(
                message_id=message_id,
                job_id=job_id,
                raw_message=csv_content,
                message_type="CSV_FILE",
                metadata={"filename": file.filename}
            )
        
        # Infer schema
        schema = csv_handler.infer_schema_from_csv(csv_content)
        
        # Convert to JSON
        data = csv_handler.csv_to_json(csv_content)
        
        return {
            "success": True,
            "filename": file.filename,
            "schema": schema,
            "rowCount": len(data),
            "preview": data[:10]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading CSV: {str(e)}")


# ============================================================================
# HL7 V2 MASTERY ENDPOINTS - Advanced Integration Engine Features
# ============================================================================

@app.post("/api/v1/hl7/parse-advanced")
async def parse_hl7_advanced(
    hl7_message: str = Body(..., embed=True),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Parse HL7 message using advanced parser with DOM tree
    
    Args:
        hl7_message: Raw HL7 v2 message
        current_user: Authenticated user
        
    Returns:
        Parsed message tree with XPath access
    """
    try:
        parser = get_hl7_advanced_parser()
        message_tree = parser.parse_message(hl7_message)
        
        return {
            "success": True,
            "messageTree": message_tree.to_dict(),
            "demographics": message_tree.get_patient_demographics(),
            "xpathSupport": True
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse HL7 message: {str(e)}")


@app.post("/api/v1/hl7/xpath-query")
async def xpath_query(
    hl7_message: str = Body(...),
    xpath: str = Body(...),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Execute XPath-like query on HL7 message
    
    Args:
        hl7_message: Raw HL7 v2 message
        xpath: XPath expression (e.g., 'PID.5.1' for last name)
        current_user: Authenticated user
        
    Returns:
        Query result
    """
    try:
        parser = get_hl7_advanced_parser()
        result = parser.xpath_query(hl7_message, xpath)
        
        return {
            "success": True,
            "xpath": xpath,
            "result": result,
            "type": type(result).__name__
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"XPath query failed: {str(e)}")


@app.post("/api/v1/routing/create-channel")
async def create_routing_channel(
    channel_name: str = Body(...),
    description: str = Body(default=""),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create new routing channel
    
    Args:
        channel_name: Unique channel name
        description: Channel description
        current_user: Authenticated user
        
    Returns:
        Channel configuration
    """
    try:
        router = get_routing_engine()
        channel = router.create_channel(channel_name, description)
        
        return {
            "success": True,
            "channel": {
                "name": channel.name,
                "description": channel.description,
                "enabled": channel.enabled,
                "ruleCount": len(channel.rules)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create channel: {str(e)}")


@app.post("/api/v1/routing/add-rule")
async def add_routing_rule(
    channel_name: str = Body(...),
    rule_name: str = Body(...),
    conditions: List[Dict] = Body(...),
    actions: List[Dict] = Body(...),
    priority: int = Body(100),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Add routing rule to channel
    
    Args:
        channel_name: Target channel name
        rule_name: Rule name
        conditions: List of condition objects
        actions: List of action objects  
        priority: Rule priority (lower = higher priority)
        current_user: Authenticated user
        
    Returns:
        Rule configuration
    """
    try:
        from routing_engine import RoutingRule
        
        router = get_routing_engine()
        channel = router.get_channel(channel_name)
        
        if not channel:
            raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found")
        
        rule = RoutingRule(rule_name, conditions, actions, priority)
        channel.add_rule(rule)
        
        return {
            "success": True,
            "rule": {
                "name": rule.name,
                "priority": rule.priority,
                "conditionCount": len(rule.conditions),
                "actionCount": len(rule.actions)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add rule: {str(e)}")


@app.post("/api/v1/routing/process")
async def process_message_routing(
    hl7_message: str = Body(...),
    channel_name: str = Body(...),
    context: Dict = Body(default={}),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Process HL7 message through routing engine
    
    Args:
        hl7_message: Raw HL7 v2 message
        channel_name: Channel to process through
        context: Additional processing context
        current_user: Authenticated user
        
    Returns:
        Processing results
    """
    try:
        router = get_routing_engine()
        result = router.process_message(hl7_message, channel_name, context)
        
        return {
            "success": True,
            "processingResult": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Message processing failed: {str(e)}")


@app.get("/api/v1/routing/channels")
async def get_routing_channels(current_user: TokenData = Depends(get_current_user)):
    """Get all routing channels and statistics"""
    try:
        router = get_routing_engine()
        stats = router.get_engine_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get channels: {str(e)}")


@app.post("/api/v1/mapping/analyze-source")
async def analyze_mapping_source(
    hl7_message: str = Body(..., embed=True),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Analyze HL7 message for visual mapping
    
    Args:
        hl7_message: Raw HL7 v2 message
        current_user: Authenticated user
        
    Returns:
        Source field analysis for mapping interface
    """
    try:
        mapper = get_visual_mapper()
        analysis = mapper.analyze_source_message(hl7_message)
        
        return {
            "success": True,
            "sourceAnalysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Source analysis failed: {str(e)}")


@app.get("/api/v1/mapping/target-schemas")
async def get_mapping_target_schemas(current_user: TokenData = Depends(get_current_user)):
    """Get available target schema options for mapping"""
    try:
        mapper = get_visual_mapper()
        schemas = mapper.get_target_schema_options()
        
        return {
            "success": True,
            "targetSchemas": schemas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schemas: {str(e)}")


@app.post("/api/v1/mapping/create-project")
async def create_mapping_project(
    project_name: str = Body(...),
    source_message: str = Body(...),
    target_schema: str = Body(...),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create visual mapping project
    
    Args:
        project_name: Name for mapping project
        source_message: HL7 source message
        target_schema: Target schema type
        current_user: Authenticated user
        
    Returns:
        Mapping project configuration
    """
    try:
        mapper = get_visual_mapper()
        project = mapper.create_mapping_project(project_name, source_message, target_schema)
        
        return {
            "success": True,
            "project": project
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Project creation failed: {str(e)}")


@app.post("/api/v1/mapping/suggest-mappings")
async def suggest_field_mappings(
    source_fields: List[Dict] = Body(...),
    target_fields: List[Dict] = Body(...),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Generate AI-powered mapping suggestions
    
    Args:
        source_fields: Source field definitions
        target_fields: Target field definitions
        current_user: Authenticated user
        
    Returns:
        Suggested mappings with confidence scores
    """
    try:
        mapper = get_visual_mapper()
        suggestions = mapper.suggest_mappings(source_fields, target_fields)
        
        return {
            "success": True,
            "suggestions": [s.to_dict() for s in suggestions],
            "suggestionCount": len(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Mapping suggestions failed: {str(e)}")


@app.post("/api/v1/mapping/execute")
async def execute_visual_mapping(
    mappings: List[Dict] = Body(...),
    source_data: Dict = Body(...),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Execute visual mappings against source data
    
    Args:
        mappings: List of mapping configurations
        source_data: Source data to transform
        current_user: Authenticated user
        
    Returns:
        Transformed data
    """
    try:
        mapper = get_visual_mapper()
        result = mapper.execute_mapping(mappings, source_data)
        
        return {
            "success": True,
            "transformedData": result,
            "mappingCount": len([m for m in mappings if m.get('enabled', True)])
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Mapping execution failed: {str(e)}")


# ============================================================================
# REAL-TIME STREAMING INGESTION ENGINE - Lightweight
# =========================================================================

@app.get("/api/v1/ingestion/connector-types")
async def get_connector_types(current_user: TokenData = Depends(get_current_user)):
    """List available connector types and configuration templates"""
    return {
        "success": True,
        "connector_types": {
            connector_type.value: {
                "name": template.get("name"),
                "description": template.get("description"),
                "config_schema": template.get("config_schema"),
                "example_config": template.get("example_config"),
            }
            for connector_type, template in CONNECTOR_TEMPLATES.items()
        },
    }


@app.post("/api/v1/ingestion/jobs")
async def create_ingestion_job(
    payload: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user),
):
    """Create a new ingestion job with source/destination connectors"""
    try:
        import uuid
        from datetime import datetime as _dt
        from ingestion_models import ConnectorType

        job_id = f"job_{int(_dt.now().timestamp())}"

        src_cfg = payload.get("source_connector_config", {})
        dst_cfg = payload.get("destination_connector_config", {})

        source_connector = ConnectorConfig(
            connector_id=f"src_{uuid.uuid4().hex[:8]}",
            connector_type=ConnectorType(src_cfg.get("connector_type")),
            name=src_cfg.get("name", "Source"),
            config=src_cfg.get("config", {}),
            enabled=bool(src_cfg.get("enabled", True)),
        )

        dest_connector = ConnectorConfig(
            connector_id=f"dest_{uuid.uuid4().hex[:8]}",
            connector_type=ConnectorType(dst_cfg.get("connector_type")),
            name=dst_cfg.get("name", "Destination"),
            config=dst_cfg.get("config", {}),
            enabled=bool(dst_cfg.get("enabled", True)),
        )

        job_config = IngestionJobConfig(
            job_id=job_id,
            job_name=payload.get("job_name", job_id),
            source_connector=source_connector,
            destination_connector=dest_connector,
            mapping_job_id=payload.get("mapping_job_id"),
            resource_type_override=payload.get("resource_type"),
            transformation_rules=payload.get("transformation_rules", []),
            schedule_config=payload.get("schedule_config", {}),
            error_handling=payload.get("error_handling", {}),
            created_by=current_user.userId,
            created_at=_dt.now(),
        )

        engine = get_ingestion_engine()
        _ = engine.create_job(job_config)

        return {
            "success": True,
            "job_id": job_id,
            "job_config": {
                "job_name": job_config.job_name,
                "source": source_connector.__dict__,
                "destination": dest_connector.__dict__,
                "mapping_job_id": job_config.mapping_job_id,
                "resource_type": job_config.resource_type_override,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create ingestion job: {str(e)}")


@app.post("/api/v1/ingestion/jobs/{job_id}/control")
async def control_ingestion_job(
    job_id: str,
    request: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user),
):
    """Start or stop an ingestion job"""
    try:
        engine = get_ingestion_engine()
        action = (request.get("action") or "").lower()

        if action == "start":
            success = await engine.start_job(job_id)
            message = "started"
        elif action == "stop":
            success = await engine.stop_job(job_id)
            message = "stopped"
        else:
            raise ValueError("action must be 'start' or 'stop'")

        return {
            "success": success,
            "job_id": job_id,
            "action": action,
            "message": f"Job {job_id} {message}",
            "status": engine.get_job_status(job_id) if success else None,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to control job: {str(e)}")


@app.get("/api/v1/ingestion/jobs")
async def list_ingestion_jobs(current_user: TokenData = Depends(get_current_user)):
    try:
        engine = get_ingestion_engine()
        return {"success": True, "jobs": engine.list_jobs()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@app.get("/api/v1/ingestion/jobs/{job_id}")
async def get_ingestion_job_status(job_id: str, current_user: TokenData = Depends(get_current_user)):
    try:
        engine = get_ingestion_engine()
        return {"success": True, "job_status": engine.get_job_status(job_id)}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@app.get("/api/v1/ingestion/engine/stats")
async def get_ingestion_engine_stats(current_user: TokenData = Depends(get_current_user)):
    try:
        engine = get_ingestion_engine()
        return {"success": True, "engine_stats": engine.get_engine_stats()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get engine stats: {str(e)}")


@app.get("/api/v1/ingestion/jobs/{job_id}/records")
async def get_ingested_records(
    job_id: str,
    limit: int = 50,
    current_user: TokenData = Depends(get_current_user)
):
    """Return recent ingested records for a given job id (MongoDB target only)."""
    try:
        from pymongo import MongoClient
        engine = get_ingestion_engine()
        status = engine.get_job_status(job_id)
        dest = status.get('destination_connector', {})
        if dest.get('connector_type') != 'mongodb':
            return {"success": True, "records": [], "message": "Destination is not MongoDB"}
        uri = dest.get('config', {}).get('uri', 'mongodb://localhost:27017')
        db_name = dest.get('config', {}).get('database', 'ehr')
        coll_name = dest.get('config', {}).get('collection', 'staging')
        client = MongoClient(uri)
        coll = client[db_name][coll_name]
        docs = list(coll.find({"job_id": job_id}).sort("ingested_at", -1).limit(int(limit)))
        # serialize ObjectId and datetime
        def ser(d):
            d = dict(d)
            d.pop('_id', None)
            if 'ingested_at' in d and hasattr(d['ingested_at'], 'isoformat'):
                d['ingested_at'] = d['ingested_at'].isoformat()
            return d
        return {"success": True, "records": [ser(x) for x in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load records: {str(e)}")


@app.get("/api/v1/ingestion/jobs/{job_id}/failed")
async def get_failed_records(
    job_id: str,
    limit: int = 50,
    current_user: TokenData = Depends(get_current_user)
):
    """Return recent failed (DLQ) records for a given job id (MongoDB target only)."""
    try:
        from pymongo import MongoClient
        engine = get_ingestion_engine()
        status = engine.get_job_status(job_id)
        dest = status.get('destination_connector', {})
        if dest.get('connector_type') != 'mongodb':
            return {"success": True, "records": [], "message": "Destination is not MongoDB"}
        uri = dest.get('config', {}).get('uri', 'mongodb://localhost:27017')
        db_name = dest.get('config', {}).get('database', 'ehr')
        base_coll = dest.get('config', {}).get('collection', 'staging')
        dlq_coll = f"{base_coll}_dlq"
        client = MongoClient(uri)
        coll = client[db_name][dlq_coll]
        docs = list(coll.find({"job_id": job_id}).sort("failed_at", -1).limit(int(limit)))
        def ser(d):
            d = dict(d)
            d.pop('_id', None)
            if 'failed_at' in d and hasattr(d['failed_at'], 'isoformat'):
                d['failed_at'] = d['failed_at'].isoformat()
            return d
        return {"success": True, "records": [ser(x) for x in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load failed records: {str(e)}")


# ============================================================================
# FHIR RESOURCE ENDPOINTS
# ============================================================================

@app.get("/api/v1/fhir/resources")
async def get_fhir_resources():
    """
    Get list of available FHIR resource types
    
    Returns:
        List of FHIR resource types with schemas
    """
    resources = fhir_resources.get_available_resources()
    return {
        "resources": resources,
        "count": len(resources)
    }


@app.post("/api/v1/fhir/predict-resource")
async def predict_fhir_resource(
    schema: Dict[str, str],
    current_user: TokenData = Depends(get_current_user)
):
    """
    Predict the most appropriate FHIR resource type for a given schema
    Uses Google Gemini AI for intelligent classification
    
    Args:
        schema: Source schema (CSV columns)
        current_user: Authenticated user
        
    Returns:
        Predicted FHIR resource with confidence and reasoning
    """
    try:
        # Use Gemini AI for prediction
        gemini = get_gemini_ai()
        prediction = gemini.predict_fhir_resource(schema)
        
        # Also load the predicted resource schema
        predicted_resource = prediction['resource']
        fhir_schema = fhir_resources.get_resource_schema(predicted_resource)
        
        return {
            "success": True,
            "predictedResource": predicted_resource,
            "confidence": prediction['confidence'],
            "reasoning": prediction['reasoning'],
            "keyIndicators": prediction.get('key_indicators', []),
            "fhirSchema": fhir_schema,
            "fhirFieldCount": len(fhir_schema)
        }
    except Exception as e:
        # Fallback to heuristic if Gemini fails
        print(f"⚠️  Gemini prediction failed, using fallback: {e}")
        return {
            "success": True,
            "predictedResource": "Patient",
            "confidence": 0.70,
            "reasoning": "Fallback prediction based on common healthcare data patterns",
            "keyIndicators": list(schema.keys())[:5],
            "fhirSchema": fhir_resources.get_resource_schema("Patient"),
            "fhirFieldCount": len(fhir_resources.get_resource_schema("Patient")),
            "note": "Using fallback prediction"
        }


@app.get("/api/v1/fhir/schema/{resource_type}")
async def get_fhir_schema(resource_type: str):
    """
    Get FHIR resource schema
    
    Args:
        resource_type: FHIR resource type (Patient, Observation, etc.)
        
    Returns:
        FHIR resource schema
    """
    schema = fhir_resources.get_resource_schema(resource_type)
    
    if not schema:
        raise HTTPException(
            status_code=404,
            detail=f"FHIR resource type '{resource_type}' not found"
        )
    
    return {
        "resourceType": resource_type,
        "schema": schema,
        "fieldCount": len(schema)
    }


@app.post("/api/v1/fhir/transform")
async def transform_to_fhir(
    resource_type: str,
    request: TransformRequest,
    current_user: TokenData = Depends(optional_auth)
):
    """
    Transform columnar data to FHIR resource and optionally store in MongoDB
    
    Args:
        resource_type: FHIR resource type
        request: Transform request with mappings and data
        current_user: Optional authenticated user
        
    Returns:
        Transformed FHIR resources
    """
    try:
        fhir_resources_list = []
        
        for columnar_row in request.sampleData:
            if isinstance(columnar_row, dict):
                # Transform to FHIR
                fhir_resource = fhir_transformer.columnar_to_fhir(
                    columnar_row,
                    request.mappings,
                    resource_type
                )
                fhir_resources_list.append(fhir_resource)
        
        # Optionally store in MongoDB
        if mongo.is_connected() and len(fhir_resources_list) > 0:
            # Could store in MongoDB FHIR collection
            pass
        
        return {
            "success": True,
            "resourceType": resource_type,
            "recordCount": len(fhir_resources_list),
            "sourceData": request.sampleData,
            "fhirResources": fhir_resources_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transforming to FHIR: {str(e)}")


# ============================================================================
# FHIR CHATBOT ENDPOINTS
# ============================================================================

from fhir_chatbot_service import get_chatbot_service

@app.post("/api/v1/chat/query")
async def chat_query(
    question: str = Body(..., embed=True),
    conversation_id: Optional[str] = Body(None, embed=True),
    current_user: TokenData = Depends(optional_auth)
):
    """
    Process natural language query using RAG pattern
    
    Args:
        question: User's natural language question
        conversation_id: Optional conversation ID for context
        
    Returns:
        {
          "answer": "string",
          "query_used": {...},
          "results_count": int,
          "conversation_id": "string"
        }
    """
    try:
        import uuid
        
        # Generate or use existing conversation ID
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Get user ID
        user_id = current_user.username if current_user else "guest"
        
        # Get conversation history for context
        history = db.get_chat_history(conversation_id, limit=10)
        
        # Get chatbot service
        chatbot = get_chatbot_service()
        
        # Execute RAG pipeline
        result = chatbot.chat(question, conversation_history=history)
        
        # Save user message
        db.save_chat_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=question
        )
        
        # Save assistant response
        import json as json_lib
        db.save_chat_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content=result['answer'],
            query_json=json_lib.dumps(result['query_used']),
            results_count=result['results_count']
        )
        
        return {
            "answer": result['answer'],
            "query_used": result['query_used'],
            "results_count": result['results_count'],
            "conversation_id": conversation_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat query error: {str(e)}")


@app.get("/api/v1/chat/history/{conversation_id}")
async def get_chat_history_endpoint(
    conversation_id: str,
    limit: int = Query(50, le=100),
    current_user: TokenData = Depends(optional_auth)
):
    """
    Get conversation history for a given conversation_id
    
    Args:
        conversation_id: Conversation ID
        limit: Maximum number of messages (default: 50, max: 100)
        
    Returns:
        List of chat messages
    """
    try:
        history = db.get_chat_history(conversation_id, limit=limit)
        return {
            "success": True,
            "conversation_id": conversation_id,
            "messages": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")


@app.post("/api/v1/chat/reset")
async def reset_conversation(
    conversation_id: str = Body(..., embed=True),
    current_user: TokenData = Depends(optional_auth)
):
    """
    Clear conversation history
    
    Args:
        conversation_id: Conversation ID to delete
        
    Returns:
        Success confirmation
    """
    try:
        db.delete_conversation(conversation_id)
        return {
            "success": True,
            "message": "Conversation cleared"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset conversation: {str(e)}")


@app.get("/api/v1/chat/conversations")
async def get_user_conversations(
    limit: int = Query(20, le=50),
    current_user: TokenData = Depends(optional_auth)
):
    """
    Get list of user's conversations
    
    Args:
        limit: Maximum number of conversations (default: 20, max: 50)
        
    Returns:
        List of conversations with metadata
    """
    try:
        user_id = current_user.username if current_user else "guest"
        conversations = db.get_user_conversations(user_id, limit=limit)
        return {
            "success": True,
            "conversations": conversations,
            "count": len(conversations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")


# Serve static frontend files
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "static")), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend for all non-API routes"""
        # If it's an API route, let FastAPI handle it
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Serve index.html for all other routes (SPA)
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
