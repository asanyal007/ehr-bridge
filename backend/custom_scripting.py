"""
Custom Scripting Engine for HL7 V2 Transformations
Implements JavaScript-like scripting capabilities for advanced transformations
"""
import re
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import math


class ScriptingContext:
    """Provides context and utilities for custom scripts"""
    
    def __init__(self, message_data: Dict = None, user_context: Dict = None):
        self.message_data = message_data or {}
        self.user_context = user_context or {}
        self.functions = self._build_function_library()
        self.variables = {}
    
    def _build_function_library(self) -> Dict[str, Any]:
        """Build library of available functions for scripts"""
        return {
            # String functions
            'upper': lambda x: str(x).upper(),
            'lower': lambda x: str(x).lower(),
            'trim': lambda x: str(x).strip(),
            'substring': lambda x, start, end=None: str(x)[start:end],
            'replace': lambda x, old, new: str(x).replace(old, new),
            'split': lambda x, delimiter: str(x).split(delimiter),
            'concat': lambda *args: ''.join(str(arg) for arg in args),
            'length': lambda x: len(str(x)),
            
            # Math functions
            'abs': abs,
            'round': round,
            'floor': math.floor,
            'ceil': math.ceil,
            'min': min,
            'max': max,
            
            # Date functions
            'today': lambda: datetime.now().strftime('%Y-%m-%d'),
            'now': lambda: datetime.now().isoformat(),
            'formatDate': self._format_date,
            'parseDate': self._parse_date,
            'dateDiff': self._date_diff,
            
            # HL7 specific functions
            'hl7Date': self._hl7_to_iso_date,
            'isoDate': self._iso_to_hl7_date,
            'hl7Gender': self._convert_gender,
            'formatPhone': self._format_phone,
            'parseName': self._parse_name,
            
            # Lookup functions
            'lookup': self._lookup_value,
            'mapCode': self._map_code,
            'validateCode': self._validate_code,
            
            # Utility functions
            'isEmpty': lambda x: not bool(str(x).strip()) if x is not None else True,
            'isNull': lambda x: x is None,
            'coalesce': lambda *args: next((arg for arg in args if arg is not None), None),
            'conditional': lambda condition, true_val, false_val: true_val if condition else false_val,
            
            # Array functions
            'join': lambda arr, separator: separator.join(str(x) for x in arr if x),
            'first': lambda arr: arr[0] if arr and len(arr) > 0 else None,
            'last': lambda arr: arr[-1] if arr and len(arr) > 0 else None,
        }
    
    def _format_date(self, date_str: str, format_str: str = '%Y-%m-%d') -> str:
        """Format date string"""
        try:
            if isinstance(date_str, str) and len(date_str) >= 8:
                # Try HL7 format first: YYYYMMDD
                if date_str.isdigit():
                    dt = datetime.strptime(date_str[:8], '%Y%m%d')
                else:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime(format_str)
        except:
            pass
        return str(date_str)
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date from various formats"""
        try:
            if isinstance(date_str, str):
                if len(date_str) >= 8 and date_str.isdigit():
                    return datetime.strptime(date_str[:8], '%Y%m%d')
                else:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            pass
        return None
    
    def _date_diff(self, date1: str, date2: str, unit: str = 'days') -> Optional[float]:
        """Calculate difference between two dates"""
        try:
            dt1 = self._parse_date(date1)
            dt2 = self._parse_date(date2)
            
            if dt1 and dt2:
                diff = (dt2 - dt1).total_seconds()
                
                if unit == 'seconds':
                    return diff
                elif unit == 'minutes':
                    return diff / 60
                elif unit == 'hours':
                    return diff / 3600
                elif unit == 'days':
                    return diff / 86400
                elif unit == 'years':
                    return diff / (365.25 * 86400)
        except:
            pass
        return None
    
    def _hl7_to_iso_date(self, hl7_date: str) -> str:
        """Convert HL7 timestamp to ISO format"""
        try:
            if not hl7_date:
                return ""
            
            # Clean the date string
            clean_date = re.sub(r'[^0-9]', '', hl7_date)
            
            if len(clean_date) >= 8:
                year = clean_date[:4]
                month = clean_date[4:6]
                day = clean_date[6:8]
                
                if len(clean_date) >= 14:
                    hour = clean_date[8:10]
                    minute = clean_date[10:12]
                    second = clean_date[12:14]
                    return f"{year}-{month}-{day}T{hour}:{minute}:{second}"
                else:
                    return f"{year}-{month}-{day}"
        except:
            pass
        return str(hl7_date)
    
    def _iso_to_hl7_date(self, iso_date: str) -> str:
        """Convert ISO date to HL7 format"""
        try:
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            return dt.strftime('%Y%m%d%H%M%S')
        except:
            return str(iso_date)
    
    def _convert_gender(self, gender: str) -> str:
        """Convert gender codes between formats"""
        hl7_to_fhir = {
            'M': 'male',
            'F': 'female',
            'O': 'other',
            'U': 'unknown'
        }
        
        fhir_to_hl7 = {v: k for k, v in hl7_to_fhir.items()}
        
        gender_upper = str(gender).upper()
        
        # HL7 to FHIR
        if gender_upper in hl7_to_fhir:
            return hl7_to_fhir[gender_upper]
        
        # FHIR to HL7
        gender_lower = str(gender).lower()
        if gender_lower in fhir_to_hl7:
            return fhir_to_hl7[gender_lower]
        
        return str(gender)
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number"""
        if not phone:
            return ""
        
        # Remove all non-digits
        digits = re.sub(r'[^0-9]', '', phone)
        
        # Format as (XXX) XXX-XXXX for 10-digit numbers
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"1-({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return phone
    
    def _parse_name(self, name_field: str) -> Dict[str, str]:
        """Parse HL7 XPN name field"""
        if not name_field:
            return {}
        
        components = name_field.split('^')
        
        return {
            'family': components[0] if len(components) > 0 else '',
            'given': components[1] if len(components) > 1 else '',
            'middle': components[2] if len(components) > 2 else '',
            'suffix': components[3] if len(components) > 3 else '',
            'prefix': components[4] if len(components) > 4 else ''
        }
    
    def _lookup_value(self, key: str, lookup_table: str) -> Optional[str]:
        """Lookup value from predefined tables"""
        # This would integrate with external lookup tables
        lookup_tables = {
            'gender_codes': {
                'M': 'Male',
                'F': 'Female',
                'O': 'Other',
                'U': 'Unknown'
            },
            'state_codes': {
                'CA': 'California',
                'NY': 'New York',
                'TX': 'Texas',
                'FL': 'Florida'
            }
        }
        
        table = lookup_tables.get(lookup_table, {})
        return table.get(key)
    
    def _map_code(self, code: str, from_system: str, to_system: str) -> Optional[str]:
        """Map codes between different coding systems"""
        # Placeholder for code mapping logic
        # In production, this would integrate with terminology services
        mappings = {
            ('icd9', 'icd10'): {
                '250.00': 'E11.9',  # Diabetes
                '401.9': 'I10',     # Hypertension
            },
            ('hl7_gender', 'fhir_gender'): {
                'M': 'male',
                'F': 'female',
                'O': 'other',
                'U': 'unknown'
            }
        }
        
        mapping_key = (from_system, to_system)
        if mapping_key in mappings:
            return mappings[mapping_key].get(code)
        
        return None
    
    def _validate_code(self, code: str, code_system: str) -> bool:
        """Validate code against coding system"""
        # Placeholder for code validation
        valid_codes = {
            'icd10': ['E11.9', 'I10', 'Z51.89'],
            'loinc': ['2339-0', '2571-8', '33747-0'],
            'gender': ['M', 'F', 'O', 'U']
        }
        
        return code in valid_codes.get(code_system, [])


class SimpleScriptEngine:
    """
    Simple JavaScript-like scripting engine for HL7 transformations
    Supports basic expressions, function calls, and variable assignment
    """
    
    def __init__(self):
        self.context = None
    
    def execute(self, script: str, context: ScriptingContext) -> Any:
        """Execute script with given context"""
        self.context = context
        
        try:
            # Simple script execution (placeholder for full JavaScript engine)
            # In production, would use PyV8, NodeJS, or similar
            
            # Handle simple function calls
            if script.strip().startswith('return '):
                expression = script.strip()[7:]  # Remove 'return '
                return self._evaluate_expression(expression)
            else:
                return self._evaluate_expression(script)
        
        except Exception as e:
            raise RuntimeError(f"Script execution failed: {str(e)}")
    
    def _evaluate_expression(self, expr: str) -> Any:
        """Evaluate simple expressions"""
        expr = expr.strip()
        
        # Function call pattern: function(args...)
        func_pattern = r'(\w+)\((.*?)\)'
        match = re.match(func_pattern, expr)
        
        if match:
            func_name = match.group(1)
            args_str = match.group(2)
            
            # Parse arguments
            args = self._parse_arguments(args_str)
            
            # Execute function
            if func_name in self.context.functions:
                func = self.context.functions[func_name]
                return func(*args)
            else:
                raise ValueError(f"Unknown function: {func_name}")
        
        # Variable access: message.field or context.variable
        if '.' in expr:
            return self._get_nested_value(expr)
        
        # String literal
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        
        if expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]
        
        # Number
        try:
            if '.' in expr:
                return float(expr)
            else:
                return int(expr)
        except ValueError:
            pass
        
        # Variable
        if expr in self.context.variables:
            return self.context.variables[expr]
        
        # Default: return as string
        return expr
    
    def _parse_arguments(self, args_str: str) -> List[Any]:
        """Parse function arguments"""
        if not args_str.strip():
            return []
        
        args = []
        current_arg = ""
        in_quotes = False
        quote_char = None
        paren_count = 0
        
        for char in args_str:
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_arg += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                current_arg += char
            elif char == '(' and not in_quotes:
                paren_count += 1
                current_arg += char
            elif char == ')' and not in_quotes:
                paren_count -= 1
                current_arg += char
            elif char == ',' and not in_quotes and paren_count == 0:
                args.append(self._evaluate_expression(current_arg.strip()))
                current_arg = ""
            else:
                current_arg += char
        
        if current_arg.strip():
            args.append(self._evaluate_expression(current_arg.strip()))
        
        return args
    
    def _get_nested_value(self, path: str) -> Any:
        """Get nested value from context"""
        parts = path.split('.')
        
        if parts[0] == 'message':
            current = self.context.message_data
            for part in parts[1:]:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            return current
        elif parts[0] == 'context':
            current = self.context.user_context
            for part in parts[1:]:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            return current
        
        return None


# Global scripting engine instance
scripting_engine = None

def get_scripting_engine() -> SimpleScriptEngine:
    """Get or create scripting engine singleton"""
    global scripting_engine
    if scripting_engine is None:
        scripting_engine = SimpleScriptEngine()
    return scripting_engine


def execute_custom_script(script: str, message_data: Dict = None, user_context: Dict = None) -> Any:
    """
    Execute custom script with context
    
    Args:
        script: JavaScript-like script code
        message_data: HL7 message data
        user_context: User-provided context
        
    Returns:
        Script execution result
    """
    engine = get_scripting_engine()
    context = ScriptingContext(message_data, user_context)
    
    return engine.execute(script, context)


# Example custom scripts for common HL7 transformations
EXAMPLE_SCRIPTS = {
    'calculate_age': '''
        // Calculate patient age from birth date
        var birthDate = message.PID['7'];  // Date of birth
        var today = today();
        return dateDiff(birthDate, today, 'years');
    ''',
    
    'format_patient_name': '''
        // Format patient name as "Last, First Middle"
        var name = parseName(message.PID['5']);
        return concat(name.family, ', ', name.given, ' ', name.middle);
    ''',
    
    'normalize_phone': '''
        // Normalize phone number format
        var phone = message.PID['13'];
        return formatPhone(phone);
    ''',
    
    'map_gender_code': '''
        // Map HL7 gender to FHIR
        var gender = message.PID['8'];
        return hl7Gender(gender);
    ''',
    
    'validate_mrn': '''
        // Validate Medical Record Number format
        var mrn = message.PID['3'];
        return !isEmpty(mrn) && length(mrn) >= 6;
    ''',
    
    'conditional_mapping': '''
        // Conditional value mapping
        var patientClass = message.PV1['2'];
        return conditional(
            patientClass === 'I', 
            'Inpatient',
            conditional(patientClass === 'O', 'Outpatient', 'Unknown')
        );
    ''',
    
    'combine_address': '''
        // Combine address components
        var addr = message.PID['11'];
        var components = split(addr, '^');
        return concat(
            components[0] || '', ', ',
            components[2] || '', ', ',
            components[3] || '', ' ',
            components[4] || ''
        );
    '''
}
