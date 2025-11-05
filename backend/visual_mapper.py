"""
Visual HL7 Mapping Engine
Provides graphical mapping interface similar to Rhapsody/Mirth Connect
"""
from typing import Dict, List, Any, Optional
import json
from dataclasses import dataclass, asdict
from hl7_parser_advanced import HL7MessageTree, HL7DataTypeConverter


@dataclass
class MappingConnection:
    """Represents a visual mapping connection between source and target"""
    id: str
    source_path: str
    target_path: str
    transformation: str = "DIRECT"
    custom_script: str = ""
    enabled: bool = True
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FieldSchema:
    """Schema definition for HL7 fields or target structure"""
    path: str
    data_type: str
    description: str
    required: bool = False
    max_length: Optional[int] = None
    sample_values: List[str] = None
    
    def __post_init__(self):
        if self.sample_values is None:
            self.sample_values = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HL7FieldExtractor:
    """Extracts field definitions from HL7 message structures"""
    
    def __init__(self):
        # HL7 V2 Field Definitions (subset)
        self.hl7_fields = {
            'MSH': {
                '1': {'desc': 'Field Separator', 'type': 'ST', 'req': True},
                '2': {'desc': 'Encoding Characters', 'type': 'ST', 'req': True},
                '3': {'desc': 'Sending Application', 'type': 'HD', 'req': True},
                '4': {'desc': 'Sending Facility', 'type': 'HD', 'req': False},
                '5': {'desc': 'Receiving Application', 'type': 'HD', 'req': True},
                '6': {'desc': 'Receiving Facility', 'type': 'HD', 'req': False},
                '7': {'desc': 'Date/Time of Message', 'type': 'TS', 'req': True},
                '9': {'desc': 'Message Type', 'type': 'MSG', 'req': True},
                '10': {'desc': 'Message Control ID', 'type': 'ST', 'req': True},
                '11': {'desc': 'Processing ID', 'type': 'PT', 'req': True},
                '12': {'desc': 'Version ID', 'type': 'VID', 'req': True}
            },
            'PID': {
                '1': {'desc': 'Set ID - PID', 'type': 'SI', 'req': False},
                '3': {'desc': 'Patient Identifier List', 'type': 'CX', 'req': True},
                '5': {'desc': 'Patient Name', 'type': 'XPN', 'req': True},
                '7': {'desc': 'Date/Time of Birth', 'type': 'TS', 'req': False},
                '8': {'desc': 'Administrative Sex', 'type': 'IS', 'req': False},
                '10': {'desc': 'Race', 'type': 'CE', 'req': False},
                '11': {'desc': 'Patient Address', 'type': 'XAD', 'req': False},
                '13': {'desc': 'Phone Number - Home', 'type': 'XTN', 'req': False},
                '19': {'desc': 'SSN Number - Patient', 'type': 'ST', 'req': False}
            },
            'PV1': {
                '1': {'desc': 'Set ID - PV1', 'type': 'SI', 'req': False},
                '2': {'desc': 'Patient Class', 'type': 'IS', 'req': True},
                '3': {'desc': 'Assigned Patient Location', 'type': 'PL', 'req': False},
                '4': {'desc': 'Admission Type', 'type': 'IS', 'req': False},
                '7': {'desc': 'Attending Doctor', 'type': 'XCN', 'req': False},
                '19': {'desc': 'Visit Number', 'type': 'CX', 'req': False},
                '44': {'desc': 'Admit Date/Time', 'type': 'TS', 'req': False}
            },
            'OBX': {
                '1': {'desc': 'Set ID - OBX', 'type': 'SI', 'req': False},
                '2': {'desc': 'Value Type', 'type': 'ID', 'req': False},
                '3': {'desc': 'Observation Identifier', 'type': 'CE', 'req': True},
                '4': {'desc': 'Observation Sub-ID', 'type': 'ST', 'req': False},
                '5': {'desc': 'Observation Value', 'type': '*', 'req': False},
                '6': {'desc': 'Units', 'type': 'CE', 'req': False},
                '7': {'desc': 'References Range', 'type': 'ST', 'req': False},
                '8': {'desc': 'Abnormal Flags', 'type': 'IS', 'req': False}
            }
        }
        
        # Component definitions for complex types
        self.component_defs = {
            'XPN': {  # Extended Person Name
                '1': 'Family Name',
                '2': 'Given Name',
                '3': 'Second/Middle Names',
                '4': 'Suffix',
                '5': 'Prefix',
                '6': 'Degree'
            },
            'XAD': {  # Extended Address
                '1': 'Street Address',
                '2': 'Other Designation',
                '3': 'City',
                '4': 'State/Province',
                '5': 'Zip/Postal Code',
                '6': 'Country'
            },
            'CX': {   # Extended Composite ID
                '1': 'ID Number',
                '2': 'Check Digit',
                '3': 'Check Digit Scheme',
                '4': 'Assigning Authority'
            }
        }
    
    def extract_message_schema(self, message_tree: HL7MessageTree) -> List[FieldSchema]:
        """Extract field schema from parsed HL7 message"""
        schema_fields = []
        
        for segment in message_tree.segments:
            segment_type = segment.segment_type
            
            if segment_type in self.hl7_fields:
                segment_def = self.hl7_fields[segment_type]
                
                for field_idx in range(1, len(segment.fields) + 1):
                    field_str = str(field_idx)
                    
                    if field_str in segment_def:
                        field_def = segment_def[field_str]
                        field_value = segment.get_field_value(field_idx)
                        
                        # Basic field
                        base_path = f"{segment_type}.{field_idx}"
                        schema_fields.append(FieldSchema(
                            path=base_path,
                            data_type=field_def['type'],
                            description=f"{segment_type}-{field_idx}: {field_def['desc']}",
                            required=field_def['req'],
                            sample_values=[field_value] if field_value else []
                        ))
                        
                        # Component fields for complex types
                        if field_def['type'] in self.component_defs and field_value:
                            component_def = self.component_defs[field_def['type']]
                            field_obj = segment.get_field(field_idx)
                            
                            if field_obj:
                                for comp_idx, comp_desc in component_def.items():
                                    comp_value = field_obj.get_component(int(comp_idx))
                                    comp_path = f"{base_path}.{comp_idx}"
                                    
                                    schema_fields.append(FieldSchema(
                                        path=comp_path,
                                        data_type='ST',  # Most components are strings
                                        description=f"{field_def['desc']} - {comp_desc}",
                                        required=False,
                                        sample_values=[str(comp_value)] if comp_value else []
                                    ))
        
        return schema_fields


class VisualMappingEngine:
    """
    Visual Mapping Engine for HL7 V2 Messages
    Provides drag-and-drop style mapping interface
    """
    
    def __init__(self):
        self.field_extractor = HL7FieldExtractor()
        self.converter = HL7DataTypeConverter()
        self.transformations = {
            'DIRECT': 'Pass through without modification',
            'TRIM': 'Remove leading/trailing whitespace',
            'UPPER': 'Convert to uppercase',
            'LOWER': 'Convert to lowercase',
            'DATE_ISO': 'Convert HL7 date to ISO format',
            'PHONE_FORMAT': 'Format phone number',
            'GENDER_FHIR': 'Convert to FHIR gender codes',
            'NAME_PARSE': 'Parse HL7 name components',
            'CUSTOM': 'Custom JavaScript transformation'
        }
    
    def analyze_source_message(self, hl7_message: str) -> Dict[str, Any]:
        """Analyze HL7 message and extract mappable fields"""
        from hl7_parser_advanced import get_hl7_advanced_parser
        
        parser = get_hl7_advanced_parser()
        message_tree = parser.parse_message(hl7_message)
        
        # Extract field schema
        source_fields = self.field_extractor.extract_message_schema(message_tree)
        
        # Group by segment for UI organization
        segments = {}
        for field in source_fields:
            segment_type = field.path.split('.')[0]
            if segment_type not in segments:
                segments[segment_type] = []
            segments[segment_type].append(field.to_dict())
        
        return {
            'messageType': message_tree.message_type,
            'messageId': message_tree.message_control_id,
            'segmentCount': len(message_tree.segments),
            'fieldCount': len(source_fields),
            'isValid': len(message_tree.errors) == 0,
            'errors': message_tree.errors,
            'segments': segments,
            'allFields': [f.to_dict() for f in source_fields]
        }
    
    def get_target_schema_options(self) -> Dict[str, Dict]:
        """Get available target schema options"""
        return {
            'fhir_patient': {
                'name': 'FHIR Patient Resource',
                'description': 'HL7 FHIR Patient resource structure',
                'fields': self._get_fhir_patient_fields()
            },
            'fhir_observation': {
                'name': 'FHIR Observation Resource', 
                'description': 'HL7 FHIR Observation resource for lab results',
                'fields': self._get_fhir_observation_fields()
            },
            'csv_generic': {
                'name': 'Generic CSV/Columnar',
                'description': 'Flat columnar structure for data warehouse',
                'fields': self._get_csv_generic_fields()
            },
            'hl7_v2': {
                'name': 'HL7 V2 Message',
                'description': 'Another HL7 V2 message format',
                'fields': self._get_hl7_v2_fields()
            }
        }
    
    def _get_fhir_patient_fields(self) -> List[Dict]:
        """FHIR Patient resource field definitions"""
        return [
            {
                'path': 'resourceType',
                'data_type': 'string',
                'description': 'Resource type (always "Patient")',
                'required': True
            },
            {
                'path': 'identifier[0].value',
                'data_type': 'string',
                'description': 'Patient identifier (MRN)',
                'required': False
            },
            {
                'path': 'name[0].family',
                'data_type': 'string',
                'description': 'Family/last name',
                'required': False
            },
            {
                'path': 'name[0].given[0]',
                'data_type': 'string',
                'description': 'First/given name',
                'required': False
            },
            {
                'path': 'gender',
                'data_type': 'code',
                'description': 'Gender (male|female|other|unknown)',
                'required': False
            },
            {
                'path': 'birthDate',
                'data_type': 'date',
                'description': 'Date of birth (YYYY-MM-DD)',
                'required': False
            },
            {
                'path': 'address[0].line[0]',
                'data_type': 'string',
                'description': 'Street address',
                'required': False
            },
            {
                'path': 'address[0].city',
                'data_type': 'string',
                'description': 'City',
                'required': False
            },
            {
                'path': 'address[0].state',
                'data_type': 'string',
                'description': 'State/province',
                'required': False
            }
        ]
    
    def _get_fhir_observation_fields(self) -> List[Dict]:
        """FHIR Observation resource field definitions"""
        return [
            {
                'path': 'resourceType',
                'data_type': 'string',
                'description': 'Resource type (always "Observation")',
                'required': True
            },
            {
                'path': 'code.coding[0].code',
                'data_type': 'string',
                'description': 'Observation code (LOINC)',
                'required': True
            },
            {
                'path': 'code.coding[0].display',
                'data_type': 'string',
                'description': 'Observation name',
                'required': False
            },
            {
                'path': 'valueQuantity.value',
                'data_type': 'decimal',
                'description': 'Numeric result value',
                'required': False
            },
            {
                'path': 'valueQuantity.unit',
                'data_type': 'string',
                'description': 'Unit of measure',
                'required': False
            },
            {
                'path': 'status',
                'data_type': 'code',
                'description': 'Observation status (final|preliminary)',
                'required': True
            }
        ]
    
    def _get_csv_generic_fields(self) -> List[Dict]:
        """Generic CSV/columnar field definitions"""
        return [
            {'path': 'patient_id', 'data_type': 'string', 'description': 'Patient identifier'},
            {'path': 'first_name', 'data_type': 'string', 'description': 'First name'},
            {'path': 'last_name', 'data_type': 'string', 'description': 'Last name'},
            {'path': 'date_of_birth', 'data_type': 'date', 'description': 'Birth date'},
            {'path': 'gender', 'data_type': 'string', 'description': 'Gender'},
            {'path': 'phone', 'data_type': 'string', 'description': 'Phone number'},
            {'path': 'address', 'data_type': 'string', 'description': 'Full address'},
            {'path': 'visit_id', 'data_type': 'string', 'description': 'Visit identifier'},
            {'path': 'admission_date', 'data_type': 'datetime', 'description': 'Admission timestamp'}
        ]
    
    def _get_hl7_v2_fields(self) -> List[Dict]:
        """HL7 V2 target message fields"""
        return [
            {'path': 'MSH.3', 'data_type': 'string', 'description': 'Sending Application'},
            {'path': 'MSH.5', 'data_type': 'string', 'description': 'Receiving Application'},
            {'path': 'PID.3.1', 'data_type': 'string', 'description': 'Patient ID'},
            {'path': 'PID.5.1', 'data_type': 'string', 'description': 'Last Name'},
            {'path': 'PID.5.2', 'data_type': 'string', 'description': 'First Name'},
            {'path': 'PID.7', 'data_type': 'string', 'description': 'Date of Birth'},
            {'path': 'PID.8', 'data_type': 'string', 'description': 'Gender'},
            {'path': 'PV1.2', 'data_type': 'string', 'description': 'Patient Class'}
        ]
    
    def create_mapping_project(self, project_name: str, source_message: str, target_schema: str) -> Dict[str, Any]:
        """Create new mapping project"""
        source_analysis = self.analyze_source_message(source_message)
        target_options = self.get_target_schema_options()
        
        target_schema_def = target_options.get(target_schema, {})
        
        return {
            'projectName': project_name,
            'createdAt': str(datetime.now()),
            'sourceAnalysis': source_analysis,
            'targetSchema': {
                'type': target_schema,
                'definition': target_schema_def
            },
            'mappings': [],
            'transformations': self.transformations
        }
    
    def suggest_mappings(self, source_fields: List[Dict], target_fields: List[Dict]) -> List[MappingConnection]:
        """AI-powered mapping suggestions"""
        suggestions = []
        
        # Simple heuristic mapping (can be enhanced with ML/AI)
        name_mappings = {
            'patient_id': ['PID.3', 'identifier'],
            'first_name': ['PID.5.2', 'given', 'name.given'],
            'last_name': ['PID.5.1', 'family', 'name.family'],
            'gender': ['PID.8', 'gender'],
            'date_of_birth': ['PID.7', 'birthDate'],
            'phone': ['PID.13', 'telecom'],
            'address': ['PID.11', 'address']
        }
        
        for target_field in target_fields:
            target_path = target_field['path']
            target_key = target_path.lower().replace('[0]', '').replace('.', '_')
            
            # Find matching source field
            best_match = None
            best_score = 0
            
            for source_field in source_fields:
                source_path = source_field['path']
                score = self._calculate_mapping_score(source_path, target_path, name_mappings)
                
                if score > best_score and score > 0.3:  # Minimum confidence threshold
                    best_match = source_field
                    best_score = score
            
            if best_match:
                # Determine transformation
                transformation = self._suggest_transformation(
                    best_match.get('data_type', ''),
                    target_field.get('data_type', ''),
                    source_path,
                    target_path
                )
                
                mapping = MappingConnection(
                    id=f"map_{len(suggestions)}",
                    source_path=best_match['path'],
                    target_path=target_path,
                    transformation=transformation,
                    notes=f"Auto-suggested (confidence: {best_score:.2f})"
                )
                suggestions.append(mapping)
        
        return suggestions
    
    def _calculate_mapping_score(self, source_path: str, target_path: str, name_mappings: Dict) -> float:
        """Calculate similarity score between source and target paths"""
        source_lower = source_path.lower()
        target_lower = target_path.lower()
        
        # Exact match
        if source_lower == target_lower:
            return 1.0
        
        # Check name mappings
        for target_key, source_patterns in name_mappings.items():
            if target_key in target_lower:
                for pattern in source_patterns:
                    if pattern.lower() in source_lower:
                        return 0.8
        
        # Partial matches
        source_parts = source_lower.split('.')
        target_parts = target_lower.split('.')
        
        common_parts = set(source_parts) & set(target_parts)
        if common_parts:
            return len(common_parts) / max(len(source_parts), len(target_parts)) * 0.6
        
        return 0.0
    
    def _suggest_transformation(self, source_type: str, target_type: str, source_path: str, target_path: str) -> str:
        """Suggest appropriate transformation based on data types and paths"""
        source_lower = source_path.lower()
        target_lower = target_path.lower()
        
        # Date transformations
        if 'date' in target_lower or target_type == 'date':
            if source_type == 'TS' or 'date' in source_lower:
                return 'DATE_ISO'
        
        # Gender transformations
        if 'gender' in target_lower and 'gender' in source_lower:
            return 'GENDER_FHIR'
        
        # Phone transformations
        if 'phone' in target_lower or 'telecom' in target_lower:
            return 'PHONE_FORMAT'
        
        # Name transformations
        if any(x in target_lower for x in ['name', 'given', 'family']):
            return 'NAME_PARSE'
        
        # Default
        return 'TRIM' if target_type == 'string' else 'DIRECT'
    
    def execute_mapping(self, mappings: List[Dict], source_data: Dict) -> Dict[str, Any]:
        """Execute mappings against source data"""
        result = {}
        
        for mapping in mappings:
            if not mapping.get('enabled', True):
                continue
            
            source_path = mapping['source_path']
            target_path = mapping['target_path']
            transformation = mapping.get('transformation', 'DIRECT')
            custom_script = mapping.get('custom_script', '')
            
            # Get source value
            source_value = self._get_nested_value(source_data, source_path)
            if source_value is None:
                continue
            
            # Apply transformation
            transformed_value = self._apply_transformation(
                source_value, transformation, custom_script
            )
            
            # Set target value
            self._set_nested_value(result, target_path, transformed_value)
        
        return result
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def _set_nested_value(self, data: Dict, path: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _apply_transformation(self, value: Any, transformation: str, custom_script: str = "") -> Any:
        """Apply transformation to value"""
        if transformation == 'DIRECT':
            return value
        elif transformation == 'TRIM':
            return str(value).strip()
        elif transformation == 'UPPER':
            return str(value).upper()
        elif transformation == 'LOWER':
            return str(value).lower()
        elif transformation == 'DATE_ISO':
            return self.converter.timestamp_to_iso(str(value))
        elif transformation == 'GENDER_FHIR':
            return self.converter.gender_code(str(value))
        elif transformation == 'PHONE_FORMAT':
            return self.converter.phone_number(str(value))
        elif transformation == 'NAME_PARSE':
            return self.converter.name_components(str(value))
        elif transformation == 'CUSTOM' and custom_script:
            # Placeholder for custom JavaScript execution
            # In production, this would use a JavaScript engine
            return f"CUSTOM({value})"
        else:
            return value


# Global visual mapper instance
visual_mapper = None

def get_visual_mapper() -> VisualMappingEngine:
    """Get or create visual mapper singleton"""
    global visual_mapper
    if visual_mapper is None:
        visual_mapper = VisualMappingEngine()
    return visual_mapper
