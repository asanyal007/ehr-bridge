"""
Advanced HL7 V2 Parser with DOM Message Tree
Implements enterprise-grade parsing similar to Rhapsody/Mirth Connect
"""
import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json


class HL7Field:
    """Represents a single HL7 field with components and subcomponents"""
    
    def __init__(self, raw_value: str = ""):
        self.raw_value = raw_value
        self.components = []
        self._parse_components()
    
    def _parse_components(self):
        """Parse components (^-delimited) and subcomponents (&-delimited)"""
        if not self.raw_value:
            return
        
        # Split by component separator (^)
        components = self.raw_value.split('^')
        
        for comp in components:
            if '&' in comp:
                # Has subcomponents
                subcomponents = comp.split('&')
                self.components.append(subcomponents)
            else:
                self.components.append(comp)
    
    def get_component(self, index: int) -> Union[str, List[str], None]:
        """Get component by index (1-based HL7 convention)"""
        if index < 1 or index > len(self.components):
            return None
        return self.components[index - 1]
    
    def get_subcomponent(self, comp_index: int, sub_index: int) -> Optional[str]:
        """Get subcomponent by component and subcomponent index"""
        component = self.get_component(comp_index)
        if isinstance(component, list) and sub_index >= 1 and sub_index <= len(component):
            return component[sub_index - 1]
        return None
    
    def __str__(self):
        return self.raw_value


class HL7Segment:
    """Represents an HL7 segment with parsed fields"""
    
    def __init__(self, raw_segment: str):
        self.raw_segment = raw_segment.strip()
        self.segment_type = ""
        self.fields = []
        self._parse_segment()
    
    def _parse_segment(self):
        """Parse segment into fields"""
        if not self.raw_segment:
            return
        
        # Handle MSH segment special case (field separator is part of MSH-2)
        if self.raw_segment.startswith('MSH'):
            self.segment_type = 'MSH'
            # MSH|^~\&|... - field separator is |, encoding chars are ^~\&
            parts = self.raw_segment.split('|')
            self.fields = [HL7Field(part) for part in parts]
        else:
            # Regular segment
            parts = self.raw_segment.split('|')
            self.segment_type = parts[0] if parts else ""
            self.fields = [HL7Field(part) for part in parts[1:]] if len(parts) > 1 else []
    
    def get_field(self, index: int) -> Optional[HL7Field]:
        """Get field by index (1-based HL7 convention)"""
        if index < 1 or index > len(self.fields):
            return None
        return self.fields[index - 1]
    
    def get_field_value(self, index: int, component: int = 1, subcomponent: int = 1) -> Optional[str]:
        """Get field value with optional component/subcomponent"""
        field = self.get_field(index)
        if not field:
            return None
        
        if component == 1 and subcomponent == 1:
            return field.raw_value
        elif subcomponent == 1:
            return str(field.get_component(component) or "")
        else:
            return field.get_subcomponent(component, subcomponent)
    
    def __str__(self):
        return f"{self.segment_type} ({len(self.fields)} fields)"


class HL7MessageTree:
    """
    Abstract Message Tree (DOM) for HL7 V2 Messages
    Provides XPath-like access to message components
    """
    
    def __init__(self, raw_message: str):
        self.raw_message = raw_message
        self.segments = []
        self.message_type = ""
        self.message_control_id = ""
        self.sender_application = ""
        self.receiver_application = ""
        self.timestamp = None
        self.errors = []
        
        # HL7 V2 Grammar Rules
        self.message_grammars = {
            'ADT^A01': ['MSH', 'EVN', 'PID', 'PV1'],
            'ADT^A08': ['MSH', 'EVN', 'PID', 'PV1'],
            'ORM^O01': ['MSH', 'PID', 'ORC', 'OBR'],
            'ORU^R01': ['MSH', 'PID', 'OBR', 'OBX'],
            'DFT^P03': ['MSH', 'EVN', 'PID', 'FT1'],
        }
        
        self._parse_message()
        self._validate_structure()
    
    def _parse_message(self):
        """Parse HL7 message into segment objects"""
        # Split by segment separator (typically \r or \n)
        segment_lines = re.split(r'[\r\n]+', self.raw_message.strip())
        
        for line in segment_lines:
            if line.strip():
                segment = HL7Segment(line.strip())
                self.segments.append(segment)
        
        # Extract message header information
        msh_segment = self.get_segment('MSH')
        if msh_segment:
            self.message_type = msh_segment.get_field_value(9)  # MSH-9
            self.message_control_id = msh_segment.get_field_value(10)  # MSH-10
            self.sender_application = msh_segment.get_field_value(3)  # MSH-3
            self.receiver_application = msh_segment.get_field_value(5)  # MSH-5
            
            # Parse timestamp MSH-7
            timestamp_str = msh_segment.get_field_value(7)
            if timestamp_str:
                try:
                    # HL7 timestamp format: YYYYMMDDHHMMSS
                    if len(timestamp_str) >= 8:
                        self.timestamp = datetime.strptime(timestamp_str[:14], '%Y%m%d%H%M%S')
                except:
                    pass
    
    def _validate_structure(self):
        """Validate message structure against HL7 V2 grammar rules"""
        if not self.message_type or self.message_type not in self.message_grammars:
            self.errors.append(f"Unknown or missing message type: {self.message_type}")
            return
        
        required_segments = self.message_grammars[self.message_type]
        present_segments = [seg.segment_type for seg in self.segments]
        
        # Check for mandatory segments
        for required_seg in required_segments:
            if required_seg not in present_segments:
                self.errors.append(f"Missing mandatory segment: {required_seg}")
        
        # MSH must be first
        if not self.segments or self.segments[0].segment_type != 'MSH':
            self.errors.append("MSH segment must be first")
    
    def get_segment(self, segment_type: str, occurrence: int = 1) -> Optional[HL7Segment]:
        """Get segment by type and occurrence number"""
        count = 0
        for segment in self.segments:
            if segment.segment_type == segment_type:
                count += 1
                if count == occurrence:
                    return segment
        return None
    
    def get_segments(self, segment_type: str) -> List[HL7Segment]:
        """Get all segments of a specific type"""
        return [seg for seg in self.segments if seg.segment_type == segment_type]
    
    def xpath(self, path: str) -> Any:
        """
        XPath-like access to message data
        Examples:
        - xpath('MSH.3') -> Sending Application
        - xpath('PID.5.1') -> Patient Last Name
        - xpath('OBX[1].5') -> First Observation Value
        """
        try:
            parts = path.split('.')
            segment_path = parts[0]
            
            # Handle array notation: PID[2] or OBX[1]
            occurrence = 1
            if '[' in segment_path and ']' in segment_path:
                segment_type = segment_path.split('[')[0]
                occurrence = int(segment_path.split('[')[1].split(']')[0])
            else:
                segment_type = segment_path
            
            segment = self.get_segment(segment_type, occurrence)
            if not segment:
                return None
            
            if len(parts) == 1:
                return segment
            
            # Field access
            field_num = int(parts[1]) if len(parts) > 1 else 1
            component = int(parts[2]) if len(parts) > 2 else 1
            subcomponent = int(parts[3]) if len(parts) > 3 else 1
            
            return segment.get_field_value(field_num, component, subcomponent)
        
        except (ValueError, IndexError) as e:
            self.errors.append(f"Invalid XPath expression: {path} - {str(e)}")
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message tree to dictionary for JSON serialization"""
        return {
            'messageType': self.message_type,
            'messageControlId': self.message_control_id,
            'senderApplication': self.sender_application,
            'receiverApplication': self.receiver_application,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'segmentCount': len(self.segments),
            'segments': [
                {
                    'type': seg.segment_type,
                    'fieldCount': len(seg.fields),
                    'raw': seg.raw_segment
                }
                for seg in self.segments
            ],
            'errors': self.errors,
            'isValid': len(self.errors) == 0
        }
    
    def get_patient_demographics(self) -> Dict[str, Any]:
        """Extract common patient demographics from PID segment"""
        pid = self.get_segment('PID')
        if not pid:
            return {}
        
        return {
            'patientId': pid.get_field_value(3, 1),  # PID-3.1
            'lastName': pid.get_field_value(5, 1),   # PID-5.1
            'firstName': pid.get_field_value(5, 2),  # PID-5.2
            'middleName': pid.get_field_value(5, 3), # PID-5.3
            'dateOfBirth': pid.get_field_value(7),   # PID-7
            'gender': pid.get_field_value(8),        # PID-8
            'race': pid.get_field_value(10),         # PID-10
            'address': {
                'street': pid.get_field_value(11, 1), # PID-11.1
                'city': pid.get_field_value(11, 3),   # PID-11.3
                'state': pid.get_field_value(11, 4),  # PID-11.4
                'zip': pid.get_field_value(11, 5),    # PID-11.5
            },
            'phoneHome': pid.get_field_value(13, 1), # PID-13.1
            'ssn': pid.get_field_value(19)           # PID-19
        }
    
    def __str__(self):
        return f"HL7 Message: {self.message_type} ({len(self.segments)} segments, {len(self.errors)} errors)"


class HL7DataTypeConverter:
    """
    HL7 V2 Data Type Conversion Utilities
    Converts HL7 data types to standard formats
    """
    
    @staticmethod
    def timestamp_to_iso(hl7_timestamp: str) -> Optional[str]:
        """Convert HL7 TS (Timestamp) to ISO 8601"""
        if not hl7_timestamp:
            return None
        
        try:
            # HL7 format: YYYYMMDD[HHMMSS[.SSSS]][+/-ZZZZ]
            # Clean format: just numbers
            clean_ts = re.sub(r'[^0-9]', '', hl7_timestamp)
            
            if len(clean_ts) >= 8:
                year = clean_ts[:4]
                month = clean_ts[4:6]
                day = clean_ts[6:8]
                
                if len(clean_ts) >= 14:
                    hour = clean_ts[8:10]
                    minute = clean_ts[10:12]
                    second = clean_ts[12:14]
                    return f"{year}-{month}-{day}T{hour}:{minute}:{second}"
                else:
                    return f"{year}-{month}-{day}"
        except:
            pass
        
        return None
    
    @staticmethod
    def gender_code(hl7_gender: str) -> str:
        """Convert HL7 gender codes to FHIR gender"""
        mapping = {
            'M': 'male',
            'F': 'female',
            'O': 'other',
            'U': 'unknown',
            '': 'unknown'
        }
        return mapping.get(hl7_gender.upper(), 'unknown')
    
    @staticmethod
    def name_components(hl7_name_field: str) -> Dict[str, str]:
        """Parse HL7 XPN (Extended Person Name) field"""
        components = hl7_name_field.split('^') if hl7_name_field else []
        
        return {
            'family': components[0] if len(components) > 0 else '',
            'given': components[1] if len(components) > 1 else '',
            'middle': components[2] if len(components) > 2 else '',
            'suffix': components[3] if len(components) > 3 else '',
            'prefix': components[4] if len(components) > 4 else '',
            'degree': components[5] if len(components) > 5 else ''
        }
    
    @staticmethod
    def phone_number(hl7_phone: str) -> str:
        """Clean and format HL7 phone number"""
        if not hl7_phone:
            return ''
        
        # Remove common HL7 phone formatting
        clean_phone = re.sub(r'[^0-9]', '', hl7_phone)
        
        # Format as (XXX) XXX-XXXX if 10 digits
        if len(clean_phone) == 10:
            return f"({clean_phone[:3]}) {clean_phone[3:6]}-{clean_phone[6:]}"
        
        return clean_phone


# Global advanced parser instance
hl7_advanced_parser = None

def get_hl7_advanced_parser():
    """Get or create advanced HL7 parser singleton"""
    global hl7_advanced_parser
    if hl7_advanced_parser is None:
        hl7_advanced_parser = HL7AdvancedParser()
    return hl7_advanced_parser


class HL7AdvancedParser:
    """Main HL7 V2 Advanced Parser Interface"""
    
    def __init__(self):
        self.converter = HL7DataTypeConverter()
    
    def parse_message(self, hl7_message: str) -> HL7MessageTree:
        """Parse HL7 message into DOM tree"""
        return HL7MessageTree(hl7_message)
    
    def validate_message(self, hl7_message: str) -> Dict[str, Any]:
        """Validate HL7 message structure and return errors"""
        tree = self.parse_message(hl7_message)
        return {
            'isValid': len(tree.errors) == 0,
            'errors': tree.errors,
            'messageType': tree.message_type,
            'segmentCount': len(tree.segments)
        }
    
    def extract_demographics(self, hl7_message: str) -> Dict[str, Any]:
        """Extract patient demographics using advanced parsing"""
        tree = self.parse_message(hl7_message)
        demographics = tree.get_patient_demographics()
        
        # Apply data type conversions
        if demographics.get('dateOfBirth'):
            demographics['dateOfBirthISO'] = self.converter.timestamp_to_iso(
                demographics['dateOfBirth']
            )
        
        if demographics.get('gender'):
            demographics['genderFHIR'] = self.converter.gender_code(
                demographics['gender']
            )
        
        return demographics
    
    def xpath_query(self, hl7_message: str, xpath: str) -> Any:
        """Execute XPath-like query on HL7 message"""
        tree = self.parse_message(hl7_message)
        return tree.xpath(xpath)
