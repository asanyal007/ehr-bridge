"""
CSV Handler for Schema Inference and Data Processing
Automatically detects column names and data types from CSV files
"""
import csv
import io
from typing import Dict, List, Any, Tuple
from datetime import datetime


class CSVHandler:
    """Handler for CSV file processing and schema inference"""
    
    def __init__(self):
        self.type_patterns = {
            'date': ['date', 'dob', 'birth', 'timestamp', 'time', 'dt'],
            'datetime': ['datetime', 'created_at', 'updated_at', 'timestamp'],
            'integer': ['age', 'count', 'number', 'qty', 'quantity', 'id'],
            'decimal': ['price', 'amount', 'rate', 'salary', 'weight', 'height'],
            'boolean': ['is_', 'has_', 'active', 'enabled', 'flag'],
        }
    
    def infer_schema_from_csv(
        self,
        csv_content: str,
        sample_rows: int = 100
    ) -> Dict[str, str]:
        """
        Infer schema from CSV content
        
        Args:
            csv_content: CSV file content as string
            sample_rows: Number of rows to sample for type inference
            
        Returns:
            Dictionary mapping column names to inferred types
        """
        # Parse CSV
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        # Get column names
        if not reader.fieldnames:
            return {}
        
        columns = list(reader.fieldnames)
        
        # Sample data for type inference
        samples = []
        for i, row in enumerate(reader):
            if i >= sample_rows:
                break
            samples.append(row)
        
        # Infer types for each column
        schema = {}
        for col in columns:
            inferred_type = self._infer_column_type(col, samples)
            schema[col] = inferred_type
        
        return schema
    
    def _infer_column_type(self, column_name: str, samples: List[Dict]) -> str:
        """
        Infer data type for a column
        
        Args:
            column_name: Column name
            samples: Sample rows
            
        Returns:
            Inferred type as string
        """
        col_lower = column_name.lower().replace('_', '').replace('-', '')
        
        # Check column name patterns first
        for type_name, patterns in self.type_patterns.items():
            if any(pattern in col_lower for pattern in patterns):
                return type_name
        
        # Check actual values
        if not samples:
            return 'string'
        
        values = [row.get(column_name, '') for row in samples if row.get(column_name)]
        
        if not values:
            return 'string'
        
        # Try to infer from values
        is_integer = all(self._is_integer(v) for v in values[:10])
        if is_integer:
            return 'integer'
        
        is_decimal = all(self._is_decimal(v) for v in values[:10])
        if is_decimal:
            return 'decimal'
        
        is_boolean = all(self._is_boolean(v) for v in values[:10])
        if is_boolean:
            return 'boolean'
        
        is_date = all(self._is_date(v) for v in values[:10])
        if is_date:
            return 'date'
        
        return 'string'
    
    def _is_integer(self, value: str) -> bool:
        """Check if value is integer"""
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _is_decimal(self, value: str) -> bool:
        """Check if value is decimal"""
        try:
            float(value)
            return '.' in str(value)
        except (ValueError, TypeError):
            return False
    
    def _is_boolean(self, value: str) -> bool:
        """Check if value is boolean"""
        value_lower = str(value).lower()
        return value_lower in ['true', 'false', '1', '0', 'yes', 'no', 't', 'f', 'y', 'n']
    
    def _is_date(self, value: str) -> bool:
        """Check if value looks like a date"""
        if not isinstance(value, str):
            return False
        
        # Common date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        ]
        
        import re
        return any(re.match(pattern, value) for pattern in date_patterns)
    
    def csv_to_json(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        Convert CSV content to JSON array
        
        Args:
            csv_content: CSV file content
            
        Returns:
            List of dictionaries
        """
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        data = []
        for row in reader:
            data.append(dict(row))
        
        return data
    
    def json_to_csv(self, data: List[Dict[str, Any]], fieldnames: List[str] = None) -> str:
        """
        Convert JSON array to CSV content
        
        Args:
            data: List of dictionaries
            fieldnames: Optional field names (inferred if not provided)
            
        Returns:
            CSV content as string
        """
        if not data:
            return ""
        
        if fieldnames is None:
            fieldnames = list(data[0].keys())
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        
        return output.getvalue()


# Global CSV handler instance
csv_handler = CSVHandler()

