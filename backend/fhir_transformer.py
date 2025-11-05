"""
FHIR Transformation Engine
Handles CSV/Columnar data to FHIR resource transformation
"""
from typing import Dict, List, Any, Optional
from fhir_resources import fhir_resources
import re
from database import get_db_manager


class FHIRTransformer:
    """Transform columnar data to FHIR resources"""
    
    def __init__(self):
        pass
    
    def columnar_to_fhir(
        self,
        columnar_data: Dict[str, Any],
        mappings: List[Dict[str, Any]],
        resource_type: str = "Patient"
    ) -> Dict[str, Any]:
        """
        Transform columnar data to FHIR resource
        
        Args:
            columnar_data: Flat dictionary of data
            mappings: List of field mappings
            resource_type: FHIR resource type
            
        Returns:
            FHIR resource JSON
        """
        # Start with template
        fhir_resource = fhir_resources.create_fhir_resource_template(resource_type)
        
        # Apply mappings
        for mapping in mappings:
            # Handle both dict and Pydantic model
            if hasattr(mapping, 'sourceField'):
                # Pydantic model
                source_field = mapping.sourceField
                target_field = mapping.targetField
                transform_type = mapping.suggestedTransform
                transform_params = mapping.transformParams or {}
            else:
                # Dictionary
                source_field = mapping.get('sourceField', '')
                target_field = mapping.get('targetField', '')
                transform_type = mapping.get('suggestedTransform', 'DIRECT')
                transform_params = mapping.get('transformParams', {})
            
            # Get value from columnar data (case-insensitive fallback)
            value = columnar_data.get(source_field)
            if value is None and isinstance(source_field, str):
                lower_map = {k.lower(): k for k in columnar_data.keys()}
                k_match = lower_map.get(source_field.lower())
                if k_match:
                    value = columnar_data.get(k_match)
            
            if value is not None:
                # Apply transformation (row-aware for CONCAT)
                transformed_value = self._apply_transformation(
                    columnar_data,
                    value,
                    transform_type,
                    transform_params
                )
                
                # Normalize target path: strip resource prefix like 'Patient.' if present
                normalized_target = target_field
                if isinstance(target_field, str) and target_field.startswith(f"{resource_type}."):
                    normalized_target = target_field[len(resource_type) + 1:]
                # Also handle capitalized resource prefixes in case-insensitive manner
                if isinstance(target_field, str) and '.' in target_field:
                    head = target_field.split('.', 1)[0]
                    if head.lower() == resource_type.lower():
                        normalized_target = target_field[len(head) + 1:]

                # Apply terminology normalization if target is code-like
                transformed_value = self._apply_normalization_if_needed(
                    normalized_target,
                    value,
                    transformed_value
                )

                # Set value in FHIR resource using path
                self._set_fhir_value(fhir_resource, normalized_target, transformed_value)
        
        return fhir_resource

    def _apply_normalization_if_needed(self, target_path: str, raw_value: Any, transformed_value: Any) -> Any:
        """If the target path looks like a code/enum, try applying saved normalization."""
        if not isinstance(raw_value, (str, int, float)):
            return transformed_value
        lower_tgt = (target_path or "").lower()
        if not any(k in lower_tgt for k in ["code", "coding", "codeableconcept", "gender", "marital", "status"]):
            return transformed_value
        db = get_db_manager()
        # Try cache first
        cached = db.get_cached_normalization(target_path, str(raw_value))
        if cached:
            # return Coding when system/code exists, else normalized scalar
            if cached.get('system') and cached.get('code'):
                return {
                    "system": cached.get('system'),
                    "code": cached.get('code'),
                    "display": cached.get('display') or str(raw_value)
                }
            return cached.get('normalized', transformed_value)
        return transformed_value
    
    def _set_fhir_value(self, resource: Dict, path: str, value: Any):
        """
        Set value in FHIR resource using dot notation path
        
        Args:
            resource: FHIR resource dictionary
            path: FHIR path like 'name[0].family' or 'address[0].city'
            value: Value to set
        """
        parts = re.split(r'\.|\[|\]', path)
        parts = [p for p in parts if p]  # Remove empty strings
        
        current = resource
        
        for i, part in enumerate(parts[:-1]):
            # Handle array indices
            if part.isdigit():
                index = int(part)
                # Ensure array exists and has enough elements
                if not isinstance(current, list):
                    return
                while len(current) <= index:
                    current.append({})
                current = current[index]
            else:
                # Handle object keys
                if part not in current:
                    # Determine if next part is an array index
                    next_part = parts[i + 1] if i + 1 < len(parts) else None
                    if next_part and next_part.isdigit():
                        current[part] = []
                    else:
                        current[part] = {}
                current = current[part]
        
        # Set final value
        final_key = parts[-1]
        if isinstance(current, list) and final_key.isdigit():
            index = int(final_key)
            while len(current) <= index:
                current.append(None)
            current[index] = value
        else:
            current[final_key] = value
    
    def _apply_transformation(
        self,
        row: Dict[str, Any],
        value: Any,
        transform_type: str,
        params: Dict[str, Any]
    ) -> Any:
        """Apply transformation for FHIR"""
        
        if transform_type == 'DIRECT':
            return value
        
        elif transform_type == 'CONCAT':
            # Join multiple field values from the source row
            if 'fields' in params and isinstance(params['fields'], list):
                separator = params.get('separator', ' ')
                out_vals: List[str] = []
                # case-insensitive lookup for each field
                lower_map = {k.lower(): k for k in row.keys()}
                for fname in params['fields']:
                    if not isinstance(fname, str):
                        continue
                    rv = row.get(fname)
                    if rv is None:
                        match = lower_map.get(fname.lower())
                        if match:
                            rv = row.get(match)
                    if rv is not None and str(rv).strip() != '':
                        out_vals.append(str(rv))
                return separator.join(out_vals)
            return value
        
        elif transform_type == 'SPLIT':
            # Split a value
            separator = params.get('separator', ' ')
            index = params.get('index', 0)
            if isinstance(value, str):
                parts = value.split(separator)
                return parts[index] if index < len(parts) else ''
            return value
        
        elif transform_type == 'FORMAT_DATE':
            # Ensure FHIR date format (YYYY-MM-DD)
            if isinstance(value, str):
                # Remove time portion if present
                if 'T' in value or ' ' in value:
                    value = value.split('T')[0].split(' ')[0]
                return value
            return value
        
        elif transform_type == 'FHIR_GENDER':
            # Map to FHIR gender codes
            gender_map = {
                'M': 'male', 'Male': 'male', 'MALE': 'male',
                'F': 'female', 'Female': 'female', 'FEMALE': 'female',
                'O': 'other', 'Other': 'other', 'OTHER': 'other',
                'U': 'unknown', 'Unknown': 'unknown', 'UNKNOWN': 'unknown'
            }
            return gender_map.get(str(value), value)
        
        elif transform_type == 'FHIR_CODE_SYSTEM':
            # Add code system for coding
            system = params.get('system', 'http://loinc.org')
            return {"system": system, "code": str(value)}
        
        elif transform_type == 'TRIM':
            return str(value).strip() if value else value
        
        elif transform_type == 'UPPERCASE':
            return str(value).upper() if value else value
        
        elif transform_type == 'LOWERCASE':
            return str(value).lower() if value else value
        
        return value


# Global FHIR transformer instance
fhir_transformer = FHIRTransformer()

