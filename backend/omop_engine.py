"""
OMOP Engine: Predict target table, preview transformed rows, and persist to MongoDB.
Lightweight PoC with simple heuristics and synthetic concept lookup.
"""
from __future__ import annotations

import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from database import get_db_manager
from mongodb_client import get_mongo_client
from omop_vocab import get_vocab_service
from person_id_service import get_person_id_service, PersonKey
from visit_id_service import get_visit_id_service, VisitKey


OMOP_TABLES = [
    "PERSON",
    "VISIT_OCCURRENCE",
    "CONDITION_OCCURRENCE",
    "MEASUREMENT",
    "DRUG_EXPOSURE",
    "OBSERVATION",
]


def predict_table_from_schema(source_schema: Dict[str, str]) -> Dict[str, Any]:
    """
    Predict top-3 OMOP tables with confidence scores using enhanced heuristics.
    Prioritizes FHIR resourceType if present.
    """
    cols = [c.lower() for c in source_schema.keys()]
    
    # PRIORITY 1: Check if this is FHIR data (has resourceType field)
    if 'resourcetype' in cols:
        # This is FHIR data - map directly from FHIR resource type to OMOP table
        fhir_to_omop = {
            'patient': 'PERSON',
            'condition': 'CONDITION_OCCURRENCE',
            'observation': 'MEASUREMENT',
            'diagnosticreport': 'MEASUREMENT',
            'medicationrequest': 'DRUG_EXPOSURE',
            'procedure': 'PROCEDURE_OCCURRENCE',
            'encounter': 'VISIT_OCCURRENCE'
        }
        
        # We need to check actual data to get the resourceType value
        # But we can infer from other FHIR-specific fields
        fhir_indicators = {
            'CONDITION_OCCURRENCE': ['code', 'category', 'clinicalstatus', 'verificationstatus', 'onsetdatetime'],
            'MEASUREMENT': ['code', 'value', 'valuequantity', 'effectivedatetime', 'performer'],
            'PERSON': ['identifier', 'active', 'name', 'telecom', 'gender', 'birthdate', 'address'],
            'DRUG_EXPOSURE': ['medicationcodableconcept', 'dosageinstruction', 'dispense'],
            'VISIT_OCCURRENCE': ['class', 'type', 'participant', 'period', 'hospitalization']
        }
        
        # Score based on FHIR-specific field patterns
        fhir_scores = {table: 0 for table in OMOP_TABLES}
        for table, indicators in fhir_indicators.items():
            for indicator in indicators:
                if indicator in cols:
                    fhir_scores[table] += 3  # High weight for FHIR fields
        
        # If we have a clear FHIR winner, return it with high confidence
        max_fhir_score = max(fhir_scores.values())
        if max_fhir_score >= 6:  # At least 2 FHIR-specific fields
            winner = max(fhir_scores, key=fhir_scores.get)
            return {
                "table": winner,
                "confidence": 0.95,
                "rationale": f"FHIR resource detected - mapped to {winner} based on FHIR schema patterns",
                "alternatives": [
                    {"table": winner, "confidence": 0.95, "rationale": "FHIR resource mapping", "score": max_fhir_score}
                ]
            }

    # PRIORITY 2: Enhanced CSV/columnar feature scoring
    scores = {t: 0 for t in OMOP_TABLES}

    # Condition indicators
    condition_terms = ["icd", "icd10", "primary_diagnosis_icd10", "diagnosis_code", "condition", "dx"]
    if any(k in cols for k in condition_terms):
        scores["CONDITION_OCCURRENCE"] += 5
    if any(k in cols for k in ["diagnosis_date", "condition_date"]):
        scores["CONDITION_OCCURRENCE"] += 2

    # Measurement indicators
    measurement_terms = ["loinc", "result", "value", "unit", "measurement", "lab", "test"]
    if any(k in cols for k in measurement_terms):
        scores["MEASUREMENT"] += 5
    if any(k in cols for k in ["measurement_date", "lab_date"]):
        scores["MEASUREMENT"] += 2

    # Drug indicators
    drug_terms = ["rxnorm", "drug", "medication", "prescription", "rx"]
    if any(k in cols for k in drug_terms):
        scores["DRUG_EXPOSURE"] += 5
    if any(k in cols for k in ["drug_date", "medication_date"]):
        scores["DRUG_EXPOSURE"] += 2

    # Visit indicators
    visit_terms = ["visit", "admit", "discharge", "encounter", "appointment"]
    if any(k in cols for k in visit_terms):
        scores["VISIT_OCCURRENCE"] += 4
    if any(k in cols for k in ["visit_date", "admit_date"]):
        scores["VISIT_OCCURRENCE"] += 2

    # Person indicators
    person_terms = ["mrn", "ssn", "first", "last", "dob", "gender", "name"]
    if any(k in cols for k in person_terms):
        scores["PERSON"] += 4
    if any(k in cols for k in ["birth_date", "date_of_birth"]):
        scores["PERSON"] += 2

    # Sort by score (descending)
    sorted_tables = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_3 = sorted_tables[:3]

    # Calculate confidences
    max_score = top_3[0][1] if top_3 else 0
    confidences = []

    for table, score in top_3:
        # Normalize confidence based on relative score
        relative_score = score / max_score if max_score > 0 else 0
        confidence = min(0.95, 0.6 + 0.3 * relative_score)
        confidences.append({
            "table": table,
            "confidence": confidence,
            "rationale": f"Heuristic match based on {score} matching schema fields",
            "score": score
        })

    # Return top prediction with alternatives
    return {
        "table": confidences[0]["table"] if confidences else "PERSON",
        "confidence": confidences[0]["confidence"] if confidences else 0.5,
        "rationale": confidences[0]["rationale"] if confidences and confidences[0]["confidence"] >= 0.7 else "Multiple possible tables - manual review recommended",
        "alternatives": confidences
    }


def _stable_id(*keys: str) -> int:
    # Coerce None to empty strings to avoid TypeError during join
    safe_keys = ["" if k is None else str(k) for k in keys]
    h = hashlib.sha256("||".join(safe_keys).encode("utf-8")).hexdigest()
    return int(h[:12], 16)  # 48-bit int


def _concept_lookup(value: str, domain: str, job_id: str = None) -> Tuple[int, int, str, str]:
    """Enhanced concept lookup: uses approved mappings first, then falls back to synthetic."""
    v = (value or "").strip()
    
    # Try to get approved concept mapping first
    if job_id:
        try:
            from database import get_db_manager
            db = get_db_manager()
            
            # Map domain to field path
            field_mapping = {
                "condition": "condition_concept_id",
                "measurement": "measurement_concept_id", 
                "drug": "drug_concept_id"
            }
            
            field_path = field_mapping.get(domain)
            if field_path:
                # Get approved mappings for this field
                normalization = db.get_terminology_normalization(job_id, field_path)
                if normalization and normalization.get('mapping'):
                    approved_mappings = normalization['mapping']
                    if v in approved_mappings:
                        concept_id = approved_mappings[v].get('concept_id', 0)
                        if concept_id > 0:
                            # Return the approved concept ID
                            return (concept_id, concept_id, "LOINC" if domain == "measurement" else "ICD10CM" if domain == "condition" else "RxNorm", v)
        except Exception as e:
            print(f"⚠️ Error getting approved mappings: {e}")
            pass
    
    # Fallback to synthetic concept lookup
    if domain == "condition" and v:
        # ICD-10 to generic concept id
        return (900000 + (abs(hash(v)) % 10000), 800000 + (abs(hash(v)) % 10000), "ICD10CM", v)
    if domain == "measurement" and v:
        return (910000 + (abs(hash(v)) % 10000), 810000 + (abs(hash(v)) % 10000), "LOINC", v)
    if domain == "drug" and v:
        return (920000 + (abs(hash(v)) % 10000), 820000 + (abs(hash(v)) % 10000), "RxNorm", v)
    return (0, 0, "", v)


def _extract_person(row: Dict[str, Any]) -> Dict[str, Any]:
    first = str(row.get("patient_first_name") or row.get("first_name") or "").strip()
    last = str(row.get("patient_last_name") or row.get("last_name") or "").strip()
    dob = str(row.get("date_of_birth") or row.get("dob") or "").strip()
    gender = str(row.get("gender") or row.get("sex") or "").strip()
    mrn = str(row.get("medical_record_number") or row.get("mrn") or "").strip()
    
    # Use PersonIDService for stable ID generation
    person_service = get_person_id_service()
    person_key = PersonKey(mrn=mrn, first_name=first, last_name=last, dob=dob)
    person_id = person_service.generate_person_id(person_key)
    
    gender_map = {"m": "M", "male": "M", "f": "F", "female": "F"}
    gender_concept_id = 8507 if gender_map.get(gender.lower(), "").upper() == "M" else 8532 if gender_map.get(gender.lower(), "").upper() == "F" else 0
    return {
        "person_id": person_id,
        "year_of_birth": int(dob[:4]) if dob[:4].isdigit() else None,
        "month_of_birth": int(dob[5:7]) if len(dob) >= 7 and dob[5:7].isdigit() else None,
        "day_of_birth": int(dob[8:10]) if len(dob) >= 10 and dob[8:10].isdigit() else None,
        "gender_concept_id": gender_concept_id,
        "mrn": mrn,
        "first_name": first,
        "last_name": last,
    }


def preview_omop(job_id: str, table: Optional[str], limit: int = 20) -> Dict[str, Any]:
    db = get_db_manager()
    job = db.get_job(job_id)
    if not job:
        return {"rows": [], "fieldCoverage": {}, "table": table or "UNKNOWN"}

    # Collect a few staged CSV rows if available
    mongo = get_mongo_client()
    rows: List[Dict[str, Any]] = []
    if mongo.is_connected():
        staged = mongo.get_messages_by_job(job_id, limit=1)
        for msg in staged:
            if msg.get('message_type') == 'CSV_FILE' and msg.get('raw_message'):
                from csv_handler import csv_handler
                parsed = csv_handler.csv_to_json(msg['raw_message'])
                rows = parsed[:limit]
                break

    # If no staged, synthesize from mapping keys (empty values)
    if not rows:
        rows = [{m.sourceField if hasattr(m, 'sourceField') else m.get('sourceField'): "" for m in (job.finalMappings or job.suggestedMappings)}]

    # Predict table if not provided
    if not table:
        table = predict_table_from_schema(job.sourceSchema)["table"]

    out_rows: List[Dict[str, Any]] = []
    for r in rows:
        person = _extract_person(r)
        if table == "CONDITION_OCCURRENCE":
            cond_code = str(r.get("primary_diagnosis_icd10") or r.get("diagnosis_code") or "").strip()
            standard_id, source_id, vocab, code = _concept_lookup(cond_code, domain="condition")
            out_rows.append({
                "person_id": person["person_id"],
                "condition_concept_id": standard_id,
                "condition_source_concept_id": source_id,
                "condition_source_value": code,
                "condition_start_date": str(r.get("diagnosis_date") or r.get("date_of_diagnosis") or ""),
            })
        elif table == "MEASUREMENT":
            loinc = str(r.get("loinc") or r.get("lab_code") or "").strip()
            standard_id, source_id, vocab, code = _concept_lookup(loinc, domain="measurement")
            out_rows.append({
                "person_id": person["person_id"],
                "measurement_concept_id": standard_id,
                "measurement_source_concept_id": source_id,
                "measurement_source_value": code,
                "value_as_number": _to_num(r.get("value") or r.get("tumor_size_mm")),
                "unit_source_value": str(r.get("unit") or "mm"),
            })
        elif table == "DRUG_EXPOSURE":
            drug = str(r.get("drug") or r.get("medication") or "").strip()
            standard_id, source_id, vocab, code = _concept_lookup(drug, domain="drug")
            out_rows.append({
                "person_id": person["person_id"],
                "drug_concept_id": standard_id,
                "drug_source_concept_id": source_id,
                "drug_source_value": code,
            })
        elif table == "PERSON":
            out_rows.append(person)
        else:
            out_rows.append(person)

    field_cov = {}
    if out_rows:
        keys = set().union(*[set(x.keys()) for x in out_rows])
        field_cov = {k: sum(1 for x in out_rows if x.get(k) not in (None, "")) / len(out_rows) for k in keys}

    return {"table": table, "rows": out_rows, "fieldCoverage": field_cov}


def persist_omop(job_id: str, table: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    mongo = get_mongo_client()
    if not mongo.is_connected():
        return {"inserted": 0}
    client = mongo.client
    db = client["ehr"]
    coll = db[f"omop_{table}"]
    docs = []
    now = datetime.utcnow()
    for r in rows:
        d = dict(r)
        d["job_id"] = job_id
        d["persisted_at"] = now
        docs.append(d)
    res = coll.insert_many(docs) if docs else None
    return {"inserted": len(res.inserted_ids) if res else 0}


def persist_all_omop(job_id: str, table: Optional[str], dry_run: bool = False, upsert: bool = True, batch_size: int = 500) -> Dict[str, Any]:
    """
    Load ALL ingested records for a job from destination Mongo collection and persist as OMOP rows.
    Supports Patient→PERSON mapping from FHIR resources and CSV-like rows via heuristic mapping.
    """
    from ingestion_engine import get_ingestion_engine
    engine = get_ingestion_engine()
    try:
        status = engine.get_job_status(job_id)
    except Exception:
        status = {}

    dest = (status or {}).get('destination_connector', {}) or {}
    connector_type = dest.get('connector_type')
    # If engine status is unavailable after restart, assume MongoDB with defaults
    if connector_type and connector_type != 'mongodb':
        return {"inserted": 0, "message": "Destination is not MongoDB"}

    uri = dest.get('config', {}).get('uri', 'mongodb://localhost:27017')
    db_name = dest.get('config', {}).get('database', 'ehr')
    coll_name = dest.get('config', {}).get('collection', 'staging')

    client = get_mongo_client().client
    db = client[db_name]
    
    # Strategy 1: Try staging collection with job_id
    coll = db[coll_name]
    docs = list(coll.find({"job_id": job_id}))
    source = f"staging collection (job_id={job_id})"
    
    # Strategy 2: If none, try to resolve ingestion job by mapping_job_id
    effective_source_job_id = job_id
    if not docs:
        try:
            jobs = engine.list_jobs()
            match = next((j for j in jobs if (j or {}).get('mapping_job_id') == job_id), None)
            if match:
                effective_source_job_id = match.get('job_id') or job_id
                docs = list(coll.find({"job_id": effective_source_job_id}))
                source = f"staging collection (resolved ingestion job_id={effective_source_job_id})"
        except Exception:
            pass
    
    # Strategy 3: Try FHIR store collections (fhir_Patient, fhir_Observation, etc.)
    if not docs:
        # Try common FHIR resource types
        for resource_type in ['Patient', 'Observation', 'Condition', 'MedicationRequest']:
            fhir_coll = db[f"fhir_{resource_type}"]
            fhir_docs = list(fhir_coll.find({"job_id": job_id}))
            if fhir_docs:
                docs = fhir_docs
                source = f"fhir_{resource_type} collection (job_id={job_id})"
                break
    
    # If still no docs, return clear error message with diagnostic info
    if not docs:
        # Provide diagnostic information about what we checked
        available_collections = [name for name in db.list_collection_names() 
                                if name.startswith('fhir_') or name == 'staging']
        
        # Check if the job_id exists in ANY collection
        found_job_ids = set()
        for coll_name in available_collections:
            sample = db[coll_name].find_one({'job_id': {'$exists': True}})
            if sample:
                found_job_ids.add(sample.get('job_id'))
        
        error_msg = (
            f"❌ No records found for job_id='{job_id}'\n\n"
            f"🔍 Searched in:\n"
            f"  - staging collection (with job_id filter)\n"
            f"  - fhir_Patient, fhir_Observation, fhir_Condition, fhir_MedicationRequest, fhir_DiagnosticReport collections\n\n"
        )
        
        if found_job_ids:
            error_msg += (
                f"💡 Available job IDs with data:\n"
                f"  {', '.join(sorted(found_job_ids)[:5])}\n\n"
            )
        
        error_msg += (
            f"✅ Possible solutions:\n"
            f"  1. Verify the job has completed ingestion\n"
            f"  2. Check if you're using the correct job ID\n"
            f"  3. Use 'OMOP Compatible' filter in the UI to see valid jobs"
        )
        
        return {
            "inserted": 0,
            "total_records_found": 0,
            "message": error_msg
        }

    # Determine table if not provided
    if not table:
        # Infer schema from first doc
        sample = docs[0]
        if isinstance(sample, dict) and sample.get('resourceType'):
            # Map FHIR resource types to OMOP tables
            resource_type = sample.get('resourceType')
            resource_to_table = {
                'Patient': 'PERSON',
                'Observation': 'MEASUREMENT',
                'Condition': 'CONDITION_OCCURRENCE',
                'MedicationRequest': 'DRUG_EXPOSURE',
                'DiagnosticReport': 'MEASUREMENT'
            }
            
            table = resource_to_table.get(resource_type)
            
            if not table:
                # Unsupported FHIR resource type
                supported_types = ', '.join(resource_to_table.keys())
                return {
                    "inserted": 0,
                    "total_records_found": len(docs),
                    "message": (
                        f"❌ Unsupported FHIR resource type: '{resource_type}'\n\n"
                        f"✅ Supported resource types:\n"
                        f"  {supported_types}\n\n"
                        f"💡 Tip: Use CSV data or supported FHIR resources for OMOP mapping."
                    )
                }
        else:
            # CSV-like schema keys
            schema = {k: 'string' for k in sample.keys()}
            table = predict_table_from_schema(schema)['table']

    out_rows: List[Dict[str, Any]] = []
    person_service = get_person_id_service()
    
    for d in docs:
        # Check if this is a FHIR resource
        is_fhir = isinstance(d, dict) and d.get('resourceType')
        
        # If FHIR resource, use the transform_fhir_to_omop function
        if is_fhir:
            resource_type = d.get('resourceType')
            
            # Use the standard FHIR-to-OMOP transformation
            transformed_rows = transform_fhir_to_omop(d, table)
            out_rows.extend(transformed_rows)
            continue
        
        # Otherwise, handle CSV-like data
        # Legacy Patient handling (for backwards compatibility)
        if isinstance(d, dict) and d.get('resourceType') == 'Patient' and table == 'PERSON':
            name = (d.get('name') or [{}])[0]
            family = (name or {}).get('family') or ''
            given_list = (name or {}).get('given') or []
            given = given_list[0] if given_list else ''
            dob = d.get('birthDate') or ''
            gender = d.get('gender') or ''
            
            # Extract MRN from identifiers
            mrn = ''
            for identifier in d.get('identifier', []):
                if identifier.get('system') == 'MRN':
                    mrn = identifier.get('value', '')
                    break
            
            # Use PersonIDService for stable ID generation
            person_key = PersonKey(mrn=mrn, first_name=given, last_name=family, dob=dob)
            person_id = person_service.generate_person_id(person_key)
            
            gender_concept_id = 8507 if (gender or '').lower().startswith('m') else 8532 if (gender or '').lower().startswith('f') else 0
            out_rows.append({
                'person_id': person_id,
                'year_of_birth': int(dob[:4]) if dob[:4].isdigit() else None,
                'month_of_birth': int(dob[5:7]) if len(dob) >= 7 and dob[5:7].isdigit() else None,
                'day_of_birth': int(dob[8:10]) if len(dob) >= 10 and dob[8:10].isdigit() else None,
                'gender_concept_id': gender_concept_id,
                'first_name': given,
                'last_name': family,
                'mrn': mrn,
            })
        else:
            # Treat as CSV-like row using preview heuristics
            person = _extract_person(d)
            if table == 'CONDITION_OCCURRENCE':
                cond_code = str(d.get("primary_diagnosis_icd10") or d.get("diagnosis_code") or "").strip()
                standard_id, source_id, vocab, code = _concept_lookup(cond_code, domain='condition', job_id=job_id)
                out_rows.append({
                    'person_id': person['person_id'],
                    'condition_concept_id': standard_id,
                    'condition_source_concept_id': source_id,
                    'condition_source_value': code,
                    'condition_start_date': str(d.get('diagnosis_date') or d.get('date_of_diagnosis') or ''),
                })
            elif table == 'MEASUREMENT':
                # Process multiple measurement types per patient
                measurements = []

                # 1. Lab measurements (from lab_code field)
                lab_code = str(d.get('lab_code') or '').strip()
                if lab_code:
                    standard_id, source_id, vocab, code = _concept_lookup(lab_code, domain='measurement', job_id=job_id)
                    measurements.append({
                        'person_id': person['person_id'],
                        'measurement_concept_id': standard_id,
                        'measurement_source_concept_id': source_id,
                        'measurement_source_value': code,
                        'value_as_number': _to_num(d.get('lab_value')),
                        'unit_source_value': str(d.get('lab_unit') or ''),
                        'measurement_date': str(d.get('lab_date') or ''),
                    })

                # 2. Vital signs - Blood Pressure Systolic
                bp_systolic = d.get('blood_pressure_systolic')
                if bp_systolic:
                    # Map to LOINC 8480-6 (Systolic blood pressure)
                    standard_id, source_id, vocab, code = _concept_lookup('8480-6', domain='measurement', job_id=job_id)
                    measurements.append({
                        'person_id': person['person_id'],
                        'measurement_concept_id': standard_id,
                        'measurement_source_concept_id': source_id,
                        'measurement_source_value': '8480-6',
                        'value_as_number': _to_num(bp_systolic),
                        'unit_source_value': 'mmHg',
                        'measurement_date': str(d.get('visit_date') or ''),
                    })

                # 3. Vital signs - Blood Pressure Diastolic
                bp_diastolic = d.get('blood_pressure_diastolic')
                if bp_diastolic:
                    # Map to LOINC 8462-4 (Diastolic blood pressure)
                    standard_id, source_id, vocab, code = _concept_lookup('8462-4', domain='measurement', job_id=job_id)
                    measurements.append({
                        'person_id': person['person_id'],
                        'measurement_concept_id': standard_id,
                        'measurement_source_concept_id': source_id,
                        'measurement_source_value': '8462-4',
                        'value_as_number': _to_num(bp_diastolic),
                        'unit_source_value': 'mmHg',
                        'measurement_date': str(d.get('visit_date') or ''),
                    })

                # 4. Vital signs - Heart Rate
                heart_rate = d.get('heart_rate')
                if heart_rate:
                    # Map to LOINC 8867-4 (Heart rate)
                    standard_id, source_id, vocab, code = _concept_lookup('8867-4', domain='measurement', job_id=job_id)
                    measurements.append({
                        'person_id': person['person_id'],
                        'measurement_concept_id': standard_id,
                        'measurement_source_concept_id': source_id,
                        'measurement_source_value': '8867-4',
                        'value_as_number': _to_num(heart_rate),
                        'unit_source_value': '/min',
                        'measurement_date': str(d.get('visit_date') or ''),
                    })

                # 5. Vital signs - Temperature
                temperature = d.get('temperature')
                if temperature:
                    # Map to LOINC 8310-5 (Body temperature)
                    standard_id, source_id, vocab, code = _concept_lookup('8310-5', domain='measurement', job_id=job_id)
                    measurements.append({
                        'person_id': person['person_id'],
                        'measurement_concept_id': standard_id,
                        'measurement_source_concept_id': source_id,
                        'measurement_source_value': '8310-5',
                        'value_as_number': _to_num(temperature),
                        'unit_source_value': 'F',
                        'measurement_date': str(d.get('visit_date') or ''),
                    })

                # 6. Vital signs - Weight
                weight = d.get('weight')
                if weight:
                    # Map to LOINC 29463-7 (Body weight)
                    standard_id, source_id, vocab, code = _concept_lookup('29463-7', domain='measurement', job_id=job_id)
                    measurements.append({
                        'person_id': person['person_id'],
                        'measurement_concept_id': standard_id,
                        'measurement_source_concept_id': source_id,
                        'measurement_source_value': '29463-7',
                        'value_as_number': _to_num(weight),
                        'unit_source_value': 'lbs',
                        'measurement_date': str(d.get('visit_date') or ''),
                    })

                # 7. Vital signs - Height
                height = d.get('height')
                if height:
                    # Map to LOINC 8302-2 (Body height)
                    standard_id, source_id, vocab, code = _concept_lookup('8302-2', domain='measurement', job_id=job_id)
                    measurements.append({
                        'person_id': person['person_id'],
                        'measurement_concept_id': standard_id,
                        'measurement_source_concept_id': source_id,
                        'measurement_source_value': '8302-2',
                        'value_as_number': _to_num(height),
                        'unit_source_value': 'in',
                        'measurement_date': str(d.get('visit_date') or ''),
                    })

                # Add all measurements to output
                out_rows.extend(measurements)
            elif table == 'DRUG_EXPOSURE':
                drug = str(d.get('drug') or d.get('medication') or '').strip()
                standard_id, source_id, vocab, code = _concept_lookup(drug, domain='drug', job_id=job_id)
                out_rows.append({
                    'person_id': person['person_id'],
                    'drug_concept_id': standard_id,
                    'drug_source_concept_id': source_id,
                    'drug_source_value': code,
                })
            elif table == 'PERSON':
                out_rows.append(person)

    # Validation & coverage
    required = {
        'PERSON': ['person_id'],
        'CONDITION_OCCURRENCE': ['person_id', 'condition_concept_id'],
        'MEASUREMENT': ['person_id', 'measurement_concept_id'],
        'DRUG_EXPOSURE': ['person_id', 'drug_concept_id']
    }.get(table, ['person_id'])
    invalid = [r for r in out_rows if any(r.get(k) in (None, '') for k in required)]
    valid_rows = [r for r in out_rows if r not in invalid]

    if dry_run:
        return {
            "table": table,
            "total": len(out_rows),
            "valid": len(valid_rows),
            "invalid": len(invalid),
            "invalid_samples": invalid[:5]
        }

    # Persist with optional upsert
    if not valid_rows:
        return {"inserted": 0, "skipped": len(invalid), "table": table}

    client = get_mongo_client().client
    db = client["ehr"]
    omop_coll = db[f"omop_{table}"]

    inserted = 0
    skipped = len(invalid)

    if upsert:
        from pymongo import UpdateOne
        ops = []
        for r in valid_rows:
            key = {
                'person_id': r.get('person_id')
            }
            if table == 'CONDITION_OCCURRENCE':
                key.update({
                    'condition_concept_id': r.get('condition_concept_id'),
                    'condition_start_date': r.get('condition_start_date')
                })
            elif table == 'MEASUREMENT':
                key.update({
                    'measurement_concept_id': r.get('measurement_concept_id'),
                    'measurement_source_value': r.get('measurement_source_value')
                })
            elif table == 'DRUG_EXPOSURE':
                key.update({
                    'drug_concept_id': r.get('drug_concept_id'),
                    'drug_source_value': r.get('drug_source_value')
                })

            doc = dict(r)
            # Persist rows under mapping job id if that was requested; else use ingestion job id
            doc['job_id'] = job_id
            doc['persisted_at'] = datetime.utcnow()
            ops.append(UpdateOne(key, {'$set': doc}, upsert=True))

            if len(ops) >= batch_size:
                res = omop_coll.bulk_write(ops, ordered=False)
                inserted += (res.upserted_count or 0) + (res.modified_count or 0)
                ops = []
        if ops:
            res = omop_coll.bulk_write(ops, ordered=False)
            inserted += (res.upserted_count or 0) + (res.modified_count or 0)
    else:
        # Insert only (may duplicate)
        for i in range(0, len(valid_rows), batch_size):
            chunk = valid_rows[i:i+batch_size]
            for r in chunk:
                r['job_id'] = job_id
                r['persisted_at'] = datetime.utcnow()
            res = omop_coll.insert_many(chunk)
            inserted += len(res.inserted_ids)

    return {
        "inserted": inserted, 
        "skipped": skipped, 
        "table": table,
        "source": source,
        "total_records_found": len(docs)
    }


def _to_num(v: Any) -> Optional[float]:
    try:
        return float(v) if v is not None and str(v) != "" else None
    except Exception:
        return None


def transform_fhir_to_omop(fhir_resource: Dict[str, Any], target_table: str) -> List[Dict[str, Any]]:
    """
    Transform a single FHIR resource into OMOP CDM format with semantic concept matching.
    Returns a list of OMOP rows (may be multiple rows from one FHIR resource).
    
    Args:
        fhir_resource: A FHIR resource dict (Patient, Observation, Condition, etc.)
        target_table: Target OMOP table name (PERSON, MEASUREMENT, CONDITION_OCCURRENCE, etc.)
    
    Returns:
        List of OMOP-formatted dictionaries with '_table' key indicating target table
    """
    resource_type = fhir_resource.get('resourceType', '')
    rows = []
    
    try:
        if resource_type == 'Patient' and target_table == 'PERSON':
            row = _transform_patient_to_person_with_semantic(fhir_resource)
            if row:
                rows.append(row)
        
        elif resource_type == 'Observation' and target_table == 'MEASUREMENT':
            row = _transform_observation_to_measurement_with_semantic(fhir_resource)
            if row:
                rows.append(row)
        
        elif resource_type == 'Condition' and target_table == 'CONDITION_OCCURRENCE':
            row = _transform_condition_to_condition_occurrence_with_semantic(fhir_resource)
            if row:
                rows.append(row)
        
        elif resource_type == 'MedicationRequest' and target_table == 'DRUG_EXPOSURE':
            row = _transform_medication_to_drug_exposure_with_semantic(fhir_resource)
            if row:
                rows.append(row)
        
        elif resource_type == 'DiagnosticReport' and target_table == 'MEASUREMENT':
            # DiagnosticReport can contain multiple measurements
            diagnostic_rows = _transform_diagnostic_report_to_measurement(fhir_resource)
            rows.extend(diagnostic_rows)
    
    except Exception as e:
        print(f"FHIR to OMOP transform error: {e}")
        pass
    
    return rows


# ============================================================================
# SEMANTIC-AWARE TRANSFORM FUNCTIONS
# ============================================================================

def _transform_patient_to_person_with_semantic(fhir_patient: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transform FHIR Patient → OMOP PERSON with semantic concept matching"""
    from person_id_service import get_person_id_service, PersonKey
    from omop_vocab import get_semantic_matcher
    from database import get_db_manager
    
    # Extract demographics
    name_obj = fhir_patient.get('name', [{}])[0] if fhir_patient.get('name') else {}
    family = name_obj.get('family', '')
    given_list = name_obj.get('given', [])
    given = given_list[0] if given_list else ''
    
    birth_date = fhir_patient.get('birthDate', '')
    gender = fhir_patient.get('gender', '')
    
    # Extract MRN
    mrn = ''
    for id_obj in fhir_patient.get('identifier', []):
        if id_obj.get('system') in ['MRN', 'urn:oid:2.16.840.1.113883.4.1']:
            mrn = id_obj.get('value', '')
            break
    
    # Generate stable person_id
    person_service = get_person_id_service()
    person_key = PersonKey(
        mrn=mrn or '',
        first_name=given or '',
        last_name=family or '',
        dob=birth_date or ''
    )
    person_id = person_service.generate_person_id(person_key)
    
    # Use semantic matching for gender concept
    gender_concept_id = 0
    if gender:
        try:
            matcher = get_semantic_matcher()
            suggestion = matcher.match_concept(
                source_code=gender,
                source_system="http://hl7.org/fhir/administrative-gender",
                source_display=gender,
                target_domain="Gender",
                context={'resourceType': 'Patient'}
            )
            
            if suggestion.confidence_score >= 0.7:
                gender_concept_id = suggestion.concept_id
            else:
                # Fallback to hardcoded mapping
                gender_concept_map = {
                    'male': 8507,  # MALE
                    'female': 8532,  # FEMALE
                    'other': 8521,  # OTHER
                    'unknown': 0
                }
                gender_concept_id = gender_concept_map.get(gender.lower(), 0)
                
                # Add to review queue if confidence is low
                if suggestion.confidence_score < 0.7:
                    db = get_db_manager()
                    db.add_to_review_queue(
                        job_id=fhir_patient.get('job_id', 'unknown'),
                        fhir_resource_id=fhir_patient.get('id', ''),
                        source_field='gender',
                        source_code=gender,
                        source_system="http://hl7.org/fhir/administrative-gender",
                        source_display=gender,
                        target_domain="Gender",
                        suggested_concept_id=gender_concept_id,
                        confidence=suggestion.confidence_score,
                        reasoning=suggestion.reasoning,
                        alternatives=str([{
                            'concept_id': alt.concept_id,
                            'concept_name': alt.concept_name,
                            'confidence': alt.confidence_score
                        } for alt in suggestion.alternatives])
                    )
        except Exception as e:
            print(f"⚠️ Semantic gender matching error: {e}")
            # Fallback to hardcoded mapping
            gender_concept_map = {
                'male': 8507,  # MALE
                'female': 8532,  # FEMALE
                'other': 8521,  # OTHER
                'unknown': 0
            }
            gender_concept_id = gender_concept_map.get(gender.lower(), 0)
    
    return {
        '_table': 'PERSON',
        'person_id': person_id,
        'gender_concept_id': gender_concept_id,
        'year_of_birth': int(birth_date[:4]) if birth_date and len(birth_date) >= 4 else None,
        'month_of_birth': int(birth_date[5:7]) if birth_date and len(birth_date) >= 7 else None,
        'day_of_birth': int(birth_date[8:10]) if birth_date and len(birth_date) >= 10 else None,
        'birth_datetime': birth_date if birth_date else None,
        'person_source_value': mrn or fhir_patient.get('id', ''),
        'gender_source_value': gender,
        'race_concept_id': 0,  # Unknown
        'ethnicity_concept_id': 0,  # Unknown
        '_confidence': getattr(suggestion, 'confidence_score', 1.0) if 'suggestion' in locals() else 1.0,
        '_reasoning': getattr(suggestion, 'reasoning', 'Direct mapping') if 'suggestion' in locals() else 'Direct mapping'
    }


def _transform_observation_to_measurement_with_semantic(fhir_obs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transform FHIR Observation → OMOP MEASUREMENT with semantic concept matching"""
    from person_id_service import get_person_id_service, PersonKey
    from omop_vocab import get_semantic_matcher
    from database import get_db_manager
    
    # Extract subject reference
    subject_ref = fhir_obs.get('subject', {}).get('reference', '')
    if not subject_ref or not subject_ref.startswith('Patient/'):
        return None
    
    # Get person_id from subject reference
    patient_id = subject_ref.replace('Patient/', '')
    person_service = get_person_id_service()
    # For now, use patient_id as person_id (in production, would lookup actual person_id)
    person_id = int(patient_id) if patient_id.isdigit() else 0
    
    # Extract measurement details
    code_obj = fhir_obs.get('code', {})
    coding = code_obj.get('coding', [{}])[0] if code_obj.get('coding') else {}
    
    value_quantity = fhir_obs.get('valueQuantity', {})
    value = value_quantity.get('value')
    unit = value_quantity.get('unit', '')
    
    effective_date = fhir_obs.get('effectiveDateTime', '')
    
    # Use semantic matching for measurement concept
    measurement_concept_id = 0
    if coding:
        try:
            matcher = get_semantic_matcher()
            suggestion = matcher.analyze_fhir_coding(coding, 'Measurement')
            
            if suggestion.confidence_score >= 0.7:
                measurement_concept_id = suggestion.concept_id
            else:
                # Add to review queue for low confidence
                db = get_db_manager()
                db.add_to_review_queue(
                    job_id=fhir_obs.get('job_id', 'unknown'),
                    fhir_resource_id=fhir_obs.get('id', ''),
                    source_field='code.coding[0]',
                    source_code=coding.get('code', ''),
                    source_system=coding.get('system', ''),
                    source_display=coding.get('display', ''),
                    target_domain='Measurement',
                    suggested_concept_id=measurement_concept_id,
                    confidence=suggestion.confidence_score,
                    reasoning=suggestion.reasoning,
                    alternatives=str([{
                        'concept_id': alt.concept_id,
                        'concept_name': alt.concept_name,
                        'confidence': alt.confidence_score
                    } for alt in suggestion.alternatives])
                )
        except Exception as e:
            print(f"⚠️ Semantic measurement matching error: {e}")
    
    return {
        '_table': 'MEASUREMENT',
        'person_id': person_id,
        'measurement_concept_id': measurement_concept_id,
        'measurement_date': effective_date[:10] if effective_date else None,
        'measurement_datetime': effective_date if effective_date else None,
        'measurement_type_concept_id': 32856,  # Lab Result
        'value_as_number': _safe_float(value),
        'unit_concept_id': 0,  # Would need semantic matching for units
        'unit_source_value': unit,
        'measurement_source_value': coding.get('code', ''),
        'measurement_source_concept_id': 0,
        '_confidence': getattr(suggestion, 'confidence_score', 1.0) if 'suggestion' in locals() else 1.0,
        '_reasoning': getattr(suggestion, 'reasoning', 'Direct mapping') if 'suggestion' in locals() else 'Direct mapping'
    }


def _transform_condition_to_condition_occurrence_with_semantic(fhir_condition: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transform FHIR Condition → OMOP CONDITION_OCCURRENCE with semantic concept matching"""
    from person_id_service import get_person_id_service, PersonKey
    from omop_vocab import get_semantic_matcher
    from database import get_db_manager
    
    # Extract subject reference
    subject_ref = fhir_condition.get('subject', {}).get('reference', '')
    if not subject_ref or not subject_ref.startswith('Patient/'):
        return None
    
    # Get person_id from subject reference
    patient_id = subject_ref.replace('Patient/', '')
    person_service = get_person_id_service()
    # For now, use patient_id as person_id (in production, would lookup actual person_id)
    person_id = int(patient_id) if patient_id.isdigit() else 0
    
    # Extract condition details
    code_obj = fhir_condition.get('code', {})
    coding = code_obj.get('coding', [{}])[0] if code_obj.get('coding') else {}
    
    onset_date = fhir_condition.get('onsetDateTime', '')
    clinical_status = fhir_condition.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', '')
    
    # Use semantic matching for condition concept
    condition_concept_id = 0
    if coding:
        try:
            matcher = get_semantic_matcher()
            suggestion = matcher.analyze_fhir_coding(coding, 'Condition')
            
            if suggestion.confidence_score >= 0.7:
                condition_concept_id = suggestion.concept_id
            else:
                # Add to review queue for low confidence
                db = get_db_manager()
                db.add_to_review_queue(
                    job_id=fhir_condition.get('job_id', 'unknown'),
                    fhir_resource_id=fhir_condition.get('id', ''),
                    source_field='code.coding[0]',
                    source_code=coding.get('code', ''),
                    source_system=coding.get('system', ''),
                    source_display=coding.get('display', ''),
                    target_domain='Condition',
                    suggested_concept_id=condition_concept_id,
                    confidence=suggestion.confidence_score,
                    reasoning=suggestion.reasoning,
                    alternatives=str([{
                        'concept_id': alt.concept_id,
                        'concept_name': alt.concept_name,
                        'confidence': alt.confidence_score
                    } for alt in suggestion.alternatives])
                )
        except Exception as e:
            print(f"⚠️ Semantic condition matching error: {e}")
    
    return {
        '_table': 'CONDITION_OCCURRENCE',
        'person_id': person_id,
        'condition_concept_id': condition_concept_id,
        'condition_start_date': onset_date[:10] if onset_date else None,
        'condition_start_datetime': onset_date if onset_date else None,
        'condition_type_concept_id': 32817,  # Primary Condition
        'condition_status_concept_id': 0,  # Would need semantic matching for status
        'condition_source_value': coding.get('code', ''),
        'condition_source_concept_id': 0,
        '_confidence': getattr(suggestion, 'confidence_score', 1.0) if 'suggestion' in locals() else 1.0,
        '_reasoning': getattr(suggestion, 'reasoning', 'Direct mapping') if 'suggestion' in locals() else 'Direct mapping'
    }


def _transform_medication_to_drug_exposure_with_semantic(fhir_med: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transform FHIR MedicationRequest → OMOP DRUG_EXPOSURE with semantic concept matching"""
    from person_id_service import get_person_id_service, PersonKey
    from omop_vocab import get_semantic_matcher
    from database import get_db_manager
    
    # Extract subject reference
    subject_ref = fhir_med.get('subject', {}).get('reference', '')
    if not subject_ref or not subject_ref.startswith('Patient/'):
        return None
    
    # Get person_id from subject reference
    patient_id = subject_ref.replace('Patient/', '')
    person_service = get_person_id_service()
    # For now, use patient_id as person_id (in production, would lookup actual person_id)
    person_id = int(patient_id) if patient_id.isdigit() else 0
    
    # Extract medication details
    medication_codeable = fhir_med.get('medicationCodeableConcept', {})
    coding = medication_codeable.get('coding', [{}])[0] if medication_codeable.get('coding') else {}
    
    authored_date = fhir_med.get('authoredOn', '')
    dosage_instruction = fhir_med.get('dosageInstruction', [{}])[0] if fhir_med.get('dosageInstruction') else {}
    dose_quantity = dosage_instruction.get('doseQuantity', {})
    
    # Use semantic matching for drug concept
    drug_concept_id = 0
    if coding:
        try:
            matcher = get_semantic_matcher()
            suggestion = matcher.analyze_fhir_coding(coding, 'Drug')
            
            if suggestion.confidence_score >= 0.7:
                drug_concept_id = suggestion.concept_id
            else:
                # Add to review queue for low confidence
                db = get_db_manager()
                db.add_to_review_queue(
                    job_id=fhir_med.get('job_id', 'unknown'),
                    fhir_resource_id=fhir_med.get('id', ''),
                    source_field='medicationCodeableConcept.coding[0]',
                    source_code=coding.get('code', ''),
                    source_system=coding.get('system', ''),
                    source_display=coding.get('display', ''),
                    target_domain='Drug',
                    suggested_concept_id=drug_concept_id,
                    confidence=suggestion.confidence_score,
                    reasoning=suggestion.reasoning,
                    alternatives=str([{
                        'concept_id': alt.concept_id,
                        'concept_name': alt.concept_name,
                        'confidence': alt.confidence_score
                    } for alt in suggestion.alternatives])
                )
        except Exception as e:
            print(f"⚠️ Semantic drug matching error: {e}")
    
    return {
        '_table': 'DRUG_EXPOSURE',
        'person_id': person_id,
        'drug_concept_id': drug_concept_id,
        'drug_exposure_start_date': authored_date[:10] if authored_date else None,
        'drug_exposure_start_datetime': authored_date if authored_date else None,
        'drug_type_concept_id': 38000177,  # Prescription
        'quantity': _safe_float(dose_quantity.get('value')),
        'unit_concept_id': 0,  # Would need semantic matching for units
        'unit_source_value': dose_quantity.get('unit', ''),
        'drug_source_value': coding.get('code', ''),
        'drug_source_concept_id': 0,
        '_confidence': getattr(suggestion, 'confidence_score', 1.0) if 'suggestion' in locals() else 1.0,
        '_reasoning': getattr(suggestion, 'reasoning', 'Direct mapping') if 'suggestion' in locals() else 'Direct mapping'
    }


# ============================================================================
# ORIGINAL TRANSFORM FUNCTIONS (for backward compatibility)
# ============================================================================

def _transform_patient_to_person(fhir_patient: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transform FHIR Patient → OMOP PERSON"""
    from person_id_service import get_person_id_service, PersonKey
    
    # Extract demographics
    name_obj = fhir_patient.get('name', [{}])[0] if fhir_patient.get('name') else {}
    family = name_obj.get('family', '')
    given_list = name_obj.get('given', [])
    given = given_list[0] if given_list else ''
    
    birth_date = fhir_patient.get('birthDate', '')
    gender = fhir_patient.get('gender', '')
    
    # Extract MRN
    mrn = ''
    for id_obj in fhir_patient.get('identifier', []):
        if id_obj.get('system') in ['MRN', 'urn:oid:2.16.840.1.113883.4.1']:
            mrn = id_obj.get('value', '')
            break
    
    # Generate stable person_id
    person_service = get_person_id_service()
    person_key = PersonKey(
        mrn=mrn or '',
        first_name=given or '',
        last_name=family or '',
        dob=birth_date or ''
    )
    person_id = person_service.generate_person_id(person_key)
    
    # Map gender to OMOP concept
    gender_concept_map = {
        'male': 8507,  # MALE
        'female': 8532,  # FEMALE
        'other': 8521,  # OTHER
        'unknown': 0
    }
    gender_concept_id = gender_concept_map.get(gender.lower(), 0)
    
    return {
        '_table': 'PERSON',
        'person_id': person_id,
        'gender_concept_id': gender_concept_id,
        'year_of_birth': int(birth_date[:4]) if birth_date and len(birth_date) >= 4 else None,
        'month_of_birth': int(birth_date[5:7]) if birth_date and len(birth_date) >= 7 else None,
        'day_of_birth': int(birth_date[8:10]) if birth_date and len(birth_date) >= 10 else None,
        'birth_datetime': birth_date if birth_date else None,
        'person_source_value': mrn or fhir_patient.get('id', ''),
        'gender_source_value': gender,
        'race_concept_id': 0,  # Unknown
        'ethnicity_concept_id': 0  # Unknown
    }


def _transform_observation_to_measurement(fhir_obs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transform FHIR Observation → OMOP MEASUREMENT"""
    from person_id_service import get_person_id_service
    
    # Extract person reference
    subject_ref = fhir_obs.get('subject', {}).get('reference', '')
    # Try to extract person_id from reference (e.g., "Patient/12345")
    person_id = None
    if '/' in subject_ref:
        person_id = subject_ref.split('/')[-1]
        try:
            person_id = int(person_id)
        except:
            person_id = None
    
    if not person_id:
        return None  # Can't create measurement without person_id
    
    # Extract measurement code
    code_obj = fhir_obs.get('code', {})
    coding_list = code_obj.get('coding', [])
    measurement_code = coding_list[0].get('code', '') if coding_list else ''
    measurement_display = coding_list[0].get('display', '') if coding_list else ''
    
    # Extract value
    value = None
    value_obj = fhir_obs.get('valueQuantity', {})
    if value_obj:
        value = value_obj.get('value')
        unit = value_obj.get('unit', '')
    
    # Extract date
    effective_date = fhir_obs.get('effectiveDateTime', '')
    measurement_date = effective_date[:10] if effective_date else None
    
    return {
        '_table': 'MEASUREMENT',
        'person_id': person_id,
        'measurement_concept_id': 0,  # Would need LOINC → OMOP lookup
        'measurement_date': measurement_date,
        'measurement_datetime': effective_date,
        'measurement_time': effective_date[11:19] if len(effective_date) > 11 else None,
        'measurement_type_concept_id': 44818702,  # Lab result
        'value_as_number': _to_num(value),
        'value_as_concept_id': 0,
        'unit_concept_id': 0,
        'unit_source_value': unit if value_obj else None,
        'measurement_source_value': measurement_code,
        'measurement_source_concept_id': 0
    }


def _transform_condition_to_condition_occurrence(fhir_condition: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transform FHIR Condition → OMOP CONDITION_OCCURRENCE"""
    
    # Extract person reference
    subject_ref = fhir_condition.get('subject', {}).get('reference', '')
    person_id = None
    if '/' in subject_ref:
        person_id = subject_ref.split('/')[-1]
        try:
            person_id = int(person_id)
        except:
            person_id = None
    
    if not person_id:
        return None
    
    # Extract condition code (ICD-10)
    code_obj = fhir_condition.get('code', {})
    coding_list = code_obj.get('coding', [])
    condition_code = coding_list[0].get('code', '') if coding_list else ''
    condition_display = coding_list[0].get('display', '') if coding_list else ''
    
    # Extract dates
    onset_date = fhir_condition.get('onsetDateTime', '')
    condition_start_date = onset_date[:10] if onset_date else None
    
    return {
        '_table': 'CONDITION_OCCURRENCE',
        'person_id': person_id,
        'condition_concept_id': 0,  # Would need ICD-10 → OMOP lookup
        'condition_start_date': condition_start_date,
        'condition_start_datetime': onset_date,
        'condition_type_concept_id': 32020,  # EHR encounter diagnosis
        'condition_status_concept_id': 0,
        'condition_source_value': condition_code,
        'condition_source_concept_id': 0
    }


def _transform_diagnostic_report_to_measurement(fhir_diagnostic: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transform FHIR DiagnosticReport → OMOP MEASUREMENT records.
    A DiagnosticReport may contain multiple result references (LOINC codes).
    """
    from person_id_service import get_person_id_service, PersonKey
    
    measurements = []
    
    # Extract person information from the diagnostic report
    # DiagnosticReport.subject should reference a Patient, but in your data it contains diagnosis text
    # We'll extract what we can
    
    patient_id = fhir_diagnostic.get('id', '')
    gender = fhir_diagnostic.get('gender', '')
    issued_date = fhir_diagnostic.get('issued', '')
    
    # Generate a person_id (you may need to improve this based on your data structure)
    person_service = get_person_id_service()
    person_key = PersonKey(
        mrn=patient_id or '',
        first_name='',
        last_name='',
        dob=''
    )
    person_id = person_service.generate_person_id(person_key)
    
    # Extract result references (LOINC codes)
    results = fhir_diagnostic.get('result', [])
    
    for result in results:
        loinc_code = result.get('reference', '') if isinstance(result, dict) else str(result)
        
        if loinc_code:
            # Create a measurement record for each LOINC code
            # You'd typically look up the LOINC code in OMOP vocabulary
            measurements.append({
                '_table': 'MEASUREMENT',
                'person_id': person_id,
                'measurement_concept_id': 900000 + (abs(hash(loinc_code)) % 10000),  # Synthetic for now
                'measurement_source_value': loinc_code,
                'measurement_date': issued_date[:10] if issued_date else None,
                'measurement_datetime': issued_date if issued_date else None,
                'measurement_type_concept_id': 44818702,  # Lab result
                'value_source_value': fhir_diagnostic.get('conclusion', '')
            })
    
    return measurements


def _transform_medication_to_drug_exposure(fhir_med: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transform FHIR MedicationRequest → OMOP DRUG_EXPOSURE"""
    
    # Extract person reference
    subject_ref = fhir_med.get('subject', {}).get('reference', '')
    person_id = None
    if '/' in subject_ref:
        person_id = subject_ref.split('/')[-1]
        try:
            person_id = int(person_id)
        except:
            person_id = None
    
    if not person_id:
        return None
    
    # Extract medication code (RxNorm)
    med_obj = fhir_med.get('medicationCodeableConcept', {})
    coding_list = med_obj.get('coding', [])
    drug_code = coding_list[0].get('code', '') if coding_list else ''
    drug_display = coding_list[0].get('display', '') if coding_list else ''
    
    # Extract dates
    authored_on = fhir_med.get('authoredOn', '')
    drug_start_date = authored_on[:10] if authored_on else None
    
    return {
        '_table': 'DRUG_EXPOSURE',
        'person_id': person_id,
        'drug_concept_id': 0,  # Would need RxNorm → OMOP lookup
        'drug_exposure_start_date': drug_start_date,
        'drug_exposure_start_datetime': authored_on,
        'drug_type_concept_id': 38000177,  # Prescription written
        'drug_source_value': drug_code,
        'drug_source_concept_id': 0,
        'route_concept_id': 0,
        'dose_unit_source_value': None
    }


