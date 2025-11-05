"""
FHIR ID Service
Generates deterministic FHIR resource IDs from demographic keys
"""
import hashlib
from typing import Dict, Any, Optional


def generate_fhir_id(resource: Dict[str, Any]) -> str:
    """
    Generates a deterministic FHIR ID for a resource based on key fields.
    
    For Patient:
      - Uses MRN, first name, last name, and DOB
    For Observation:
      - Uses code, subject reference, and effective date
    For other resources:
      - Falls back to hash of entire resource
    
    Returns:
      16-character hex string suitable for FHIR id field
    """
    resource_type = resource.get("resourceType")
    key_string = ""

    if resource_type == "Patient":
        # Extract MRN from identifiers
        mrn = ""
        for id_obj in resource.get("identifier", []):
            if id_obj.get("system") == "MRN":
                mrn = id_obj.get("value", "")
                break
        
        # Extract name components
        name_parts = resource.get("name", [{}])[0] if resource.get("name") else {}
        family = name_parts.get("family", "")
        given_list = name_parts.get("given", [])
        given = given_list[0] if given_list else ""
        
        # Extract birth date
        birth_date = resource.get("birthDate", "")
        
        key_string = f"Patient|{mrn}|{family}|{given}|{birth_date}"
    
    elif resource_type == "Observation":
        # Extract observation code
        code = resource.get("code", {}).get("coding", [{}])[0].get("code", "")
        
        # Extract subject reference
        subject_ref = resource.get("subject", {}).get("reference", "")
        
        # Extract effective date
        effective_date = resource.get("effectiveDateTime", "")
        
        key_string = f"Observation|{code}|{subject_ref}|{effective_date}"
    
    elif resource_type == "Condition":
        # Extract condition code
        code = resource.get("code", {}).get("coding", [{}])[0].get("code", "")
        
        # Extract subject reference
        subject_ref = resource.get("subject", {}).get("reference", "")
        
        # Extract onset date
        onset_date = resource.get("onsetDateTime", "")
        
        key_string = f"Condition|{code}|{subject_ref}|{onset_date}"
    
    elif resource_type == "MedicationRequest":
        # Extract medication code
        med_code = resource.get("medicationCodeableConcept", {}).get("coding", [{}])[0].get("code", "")
        
        # Extract subject reference
        subject_ref = resource.get("subject", {}).get("reference", "")
        
        # Extract authored date
        authored_on = resource.get("authoredOn", "")
        
        key_string = f"MedicationRequest|{med_code}|{subject_ref}|{authored_on}"
    
    # Fallback: hash entire resource if no specific keys found
    if not key_string:
        key_string = str(resource)
    
    # Generate SHA-256 hash and return first 16 characters
    hash_obj = hashlib.sha256(key_string.encode("utf-8"))
    return hash_obj.hexdigest()[:16]


def enrich_fhir_resource(resource: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriches a FHIR resource with:
    - Deterministic 'id' if not present
    - 'meta.lastUpdated' timestamp
    
    Modifies resource in place and returns it.
    """
    from datetime import datetime
    
    # Generate ID if not present
    if "id" not in resource or not resource["id"]:
        resource["id"] = generate_fhir_id(resource)
    
    # Add/update meta.lastUpdated
    if "meta" not in resource:
        resource["meta"] = {}
    resource["meta"]["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
    
    return resource
