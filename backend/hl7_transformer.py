"""
HL7 Transformation Engine
Handles bi-directional transformations: HL7 ↔ Columnar
"""
from typing import Dict, List, Any, Tuple
from datetime import datetime
import re


class HL7Transformer:
    """
    Bi-directional transformer for HL7 v2 messages and columnar data
    """
    
    def __init__(self):
        # HL7 delimiters
        self.field_sep = '|'
        self.component_sep = '^'
        self.repetition_sep = '~'
        self.escape_char = '\\'
        self.subcomponent_sep = '&'
    
    def hl7_to_columnar(
        self,
        hl7_message: str,
        mappings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Transform HL7 v2 message to columnar (flat) format
        
        Args:
            hl7_message: Raw HL7 message
            mappings: List of field mappings
            
        Returns:
            Columnar data dictionary
        """
        # Parse HL7 message into segments
        segments = self._parse_hl7(hl7_message)
        
        # Apply mappings
        columnar_data = {}
        
        for mapping in mappings:
            source_field = mapping.get('sourceField', '')
            target_field = mapping.get('targetField', '')
            transform_type = mapping.get('suggestedTransform', 'DIRECT')
            
            # Extract value from HL7
            value = self._extract_hl7_field(segments, source_field)
            
            if value is not None:
                # Apply transformation
                transformed_value = self._apply_transformation(
                    value,
                    transform_type,
                    mapping.get('transformParams', {})
                )
                
                columnar_data[target_field] = transformed_value
        
        return columnar_data
    
    def columnar_to_hl7(
        self,
        columnar_data: Dict[str, Any],
        mappings: List[Dict[str, Any]],
        message_template: str = None
    ) -> str:
        """
        Transform columnar data to HL7 v2 message
        
        Args:
            columnar_data: Flat data dictionary
            mappings: List of field mappings (reversed)
            message_template: Optional HL7 template
            
        Returns:
            HL7 v2 message string
        """
        # Start with template or create basic structure
        if message_template:
            hl7_message = message_template
        else:
            hl7_message = self._create_hl7_template()
        
        # Parse existing message
        segments = self._parse_hl7(hl7_message)
        
        # Apply reverse mappings
        for mapping in mappings:
            source_field = mapping.get('sourceField', '')  # Now columnar field
            target_field = mapping.get('targetField', '')  # Now HL7 field
            transform_type = mapping.get('suggestedTransform', 'DIRECT')
            
            # Get value from columnar data
            value = columnar_data.get(source_field)
            
            if value is not None:
                # Apply reverse transformation
                transformed_value = self._apply_reverse_transformation(
                    value,
                    transform_type,
                    mapping.get('transformParams', {})
                )
                
                # Insert into HL7 structure
                segments = self._insert_hl7_field(
                    segments,
                    target_field,
                    transformed_value
                )
        
        # Reconstruct HL7 message
        return self._reconstruct_hl7(segments)
    
    def _parse_hl7(self, hl7_message: str) -> Dict[str, List[List[str]]]:
        """
        Parse HL7 message into structured segments
        
        Returns:
            Dictionary of segments with fields
        """
        segments = {}
        
        for line in hl7_message.strip().split('\n'):
            if not line.strip():
                continue
            
            fields = line.split(self.field_sep)
            segment_type = fields[0] if fields else None
            
            if segment_type:
                if segment_type not in segments:
                    segments[segment_type] = []
                
                # Parse components within fields
                parsed_fields = []
                for field in fields[1:]:  # Skip segment type
                    components = field.split(self.component_sep)
                    parsed_fields.append(components)
                
                segments[segment_type].append(parsed_fields)
        
        return segments
    
    def _extract_hl7_field(
        self,
        segments: Dict[str, List[List[str]]],
        field_path: str
    ) -> Any:
        """
        Extract value from HL7 structure using path like PID-5.1
        
        Args:
            segments: Parsed HL7 segments
            field_path: Path like "PID-5.1" or "OBX-3"
            
        Returns:
            Extracted value
        """
        # Parse field path
        match = re.match(r'([A-Z]{3})-(\d+)(?:\.(\d+))?(?:\.(\d+))?', field_path)
        if not match:
            return None
        
        segment_type = match.group(1)
        field_num = int(match.group(2))
        component_num = int(match.group(3)) if match.group(3) else None
        subcomponent_num = int(match.group(4)) if match.group(4) else None
        
        # Get segment
        if segment_type not in segments or not segments[segment_type]:
            return None
        
        # Use first occurrence of segment
        segment = segments[segment_type][0]
        
        # Get field (adjust for 0-based indexing)
        if field_num - 1 >= len(segment):
            return None
        
        field = segment[field_num - 1]
        
        # Get component if specified
        if component_num is not None:
            if component_num - 1 >= len(field):
                return None
            return field[component_num - 1]
        
        # Return whole field (joined components)
        return self.component_sep.join(field) if field else None
    
    def _insert_hl7_field(
        self,
        segments: Dict[str, List[List[str]]],
        field_path: str,
        value: Any
    ) -> Dict[str, List[List[str]]]:
        """
        Insert value into HL7 structure
        
        Args:
            segments: Parsed HL7 segments
            field_path: Path like "PID-5.1"
            value: Value to insert
            
        Returns:
            Updated segments
        """
        # Parse field path
        match = re.match(r'([A-Z]{3})-(\d+)(?:\.(\d+))?', field_path)
        if not match:
            return segments
        
        segment_type = match.group(1)
        field_num = int(match.group(2))
        component_num = int(match.group(3)) if match.group(3) else None
        
        # Ensure segment exists
        if segment_type not in segments:
            segments[segment_type] = [[]]
        
        segment = segments[segment_type][0]
        
        # Ensure field exists
        while len(segment) < field_num:
            segment.append([])
        
        # Insert value
        if component_num is not None:
            # Ensure components exist
            while len(segment[field_num - 1]) < component_num:
                segment[field_num - 1].append('')
            segment[field_num - 1][component_num - 1] = str(value)
        else:
            # Replace entire field
            segment[field_num - 1] = [str(value)]
        
        return segments
    
    def _reconstruct_hl7(self, segments: Dict[str, List[List[str]]]) -> str:
        """
        Reconstruct HL7 message from parsed segments
        
        Args:
            segments: Parsed segments
            
        Returns:
            HL7 message string
        """
        lines = []
        
        # Standard segment order
        segment_order = ['MSH', 'PID', 'PV1', 'OBR', 'OBX', 'NTE']
        
        for segment_type in segment_order:
            if segment_type in segments:
                for segment in segments[segment_type]:
                    # Reconstruct fields
                    fields = []
                    for field in segment:
                        fields.append(self.component_sep.join(field))
                    
                    line = segment_type + self.field_sep + self.field_sep.join(fields)
                    lines.append(line)
        
        # Add any remaining segments
        for segment_type, segment_list in segments.items():
            if segment_type not in segment_order:
                for segment in segment_list:
                    fields = []
                    for field in segment:
                        fields.append(self.component_sep.join(field))
                    
                    line = segment_type + self.field_sep + self.field_sep.join(fields)
                    lines.append(line)
        
        return '\n'.join(lines)
    
    def _create_hl7_template(self) -> str:
        """Create basic HL7 message template"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        template = f"""MSH|^~\\&|SENDING_APP|SENDING_FACILITY|RECEIVING_APP|RECEIVING_FACILITY|{timestamp}||ADT^A01|MSG{timestamp}|P|2.5
PID|||||||||||||||||||
PV1||||||||||||||||||||||||||||||||||||||||||
"""
        return template.strip()
    
    def _apply_transformation(
        self,
        value: Any,
        transform_type: str,
        params: Dict[str, Any]
    ) -> Any:
        """Apply transformation to value (HL7 → Columnar)"""
        
        if transform_type == 'DIRECT':
            return value
        
        elif transform_type == 'CONCAT':
            # For HL7, this might join components
            if isinstance(value, list):
                separator = params.get('separator', ' ')
                return separator.join(str(v) for v in value if v)
            return value
        
        elif transform_type == 'SPLIT':
            # Split HL7 component
            separator = params.get('separator', '^')
            if isinstance(value, str):
                parts = value.split(separator)
                index = params.get('index', 0)
                return parts[index] if index < len(parts) else ''
            return value
        
        elif transform_type == 'FORMAT_DATE':
            # HL7 dates are typically YYYYMMDD
            if isinstance(value, str) and len(value) >= 8:
                try:
                    # Parse HL7 date
                    year = value[0:4]
                    month = value[4:6]
                    day = value[6:8]
                    return f"{year}-{month}-{day}"
                except:
                    return value
            return value
        
        elif transform_type == 'TRIM':
            return str(value).strip() if value else value
        
        return value
    
    def _apply_reverse_transformation(
        self,
        value: Any,
        transform_type: str,
        params: Dict[str, Any]
    ) -> Any:
        """Apply reverse transformation (Columnar → HL7)"""
        
        if transform_type == 'DIRECT':
            return value
        
        elif transform_type == 'SPLIT':
            # Reverse: join back with separator
            # This would need original data - simplified here
            return value
        
        elif transform_type == 'FORMAT_DATE':
            # Convert ISO date back to HL7 format (YYYYMMDD)
            if isinstance(value, str) and '-' in value:
                try:
                    parts = value.split('-')
                    return ''.join(parts)  # YYYYMMDD
                except:
                    return value
            return value
        
        elif transform_type == 'TRIM':
            return str(value).strip() if value else value
        
        return value


# Global transformer instance
hl7_transformer = HL7Transformer()

