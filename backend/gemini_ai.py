"""
Google Gemini AI Integration
Used for high-level FHIR resource classification and complex reasoning tasks
"""
import os
import json
from typing import Dict, List, Any
import google.generativeai as genai


class GeminiAI:
    """
    Google Gemini AI for healthcare data classification
    Predicts FHIR resource types and provides clinical insights
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize Gemini AI
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "AIzaSyCwfd_DHnKMYOWMbqX5VVTmyRNBv-Ni5vI")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 2.0 Flash (free tier compatible)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        print(f"✅ Gemini AI initialized (gemini-2.0-flash-exp)")
    
    def predict_fhir_resource(self, csv_schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Predict the most appropriate FHIR resource type for a CSV schema
        
        Args:
            csv_schema: Dictionary of CSV column names to types
            
        Returns:
            Dictionary with predicted resource, confidence, and reasoning
        """
        # Create prompt for Gemini
        columns = list(csv_schema.keys())
        schema_description = json.dumps(csv_schema, indent=2)
        
        prompt = f"""You are a healthcare data interoperability expert. Analyze this CSV schema and determine the SINGLE most appropriate FHIR R4 resource type.

CSV Schema:
{schema_description}

Column Names: {', '.join(columns)}

Available FHIR Resources:
- Patient (demographics, identifiers, contact info)
- Observation (lab results, vitals, measurements)
- Condition (diagnoses, problems, health concerns)
- Procedure (surgeries, treatments performed)
- Encounter (hospital visits, appointments)
- MedicationRequest (prescriptions, medication orders)
- DiagnosticReport (imaging, pathology reports)

Based on the CSV column names and data types, which FHIR resource is the BEST match?

Respond ONLY with valid JSON in this exact format:
{{
  "resource": "Patient",
  "confidence": 0.95,
  "reasoning": "Contains patient demographics including name, DOB, gender, and identifiers",
  "key_indicators": ["PatientFirstName", "PatientLastName", "DateOfBirth", "Gender"]
}}

JSON Response:"""
        
        try:
            # Generate response
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            # Sometimes Gemini wraps JSON in markdown code blocks
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate result
            if 'resource' not in result:
                raise ValueError("No resource field in response")
            
            # Ensure confidence is set
            if 'confidence' not in result:
                result['confidence'] = 0.85
            
            return result
            
        except Exception as e:
            print(f"⚠️  Gemini prediction error: {e}")
            # Fallback to heuristic-based prediction
            return self._fallback_prediction(csv_schema)

    # ------------------------------
    # Terminology helpers
    # ------------------------------
    def suggest_code_system(self, sample_values: List[str]) -> Dict[str, Any]:
        """
        Suggest likely code system (ICD-10-CM, SNOMED CT, LOINC, RxNorm, FHIR value sets)
        based on sample values and clinical context.
        Returns { system, confidence, rationale }
        """
        prompt = (
            "You are a clinical terminology expert. Given sample codes/values, identify the most "
            "likely code system among: ICD-10-CM, SNOMED CT, LOINC, RxNorm, FHIR AdministrativeGender, "
            "FHIR MaritalStatus, or 'UNKNOWN'. Provide JSON {system, confidence, rationale}.\n"
            f"Samples: {sample_values[:20]}\nJSON only:"
        )
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            data = json.loads(text)
            if 'system' not in data:
                raise ValueError('No system field')
            if 'confidence' not in data:
                data['confidence'] = 0.8
            return data
        except Exception as e:
            return {"system": "UNKNOWN", "confidence": 0.5, "rationale": f"fallback: {e}"}

    def suggest_code_entries(self, sample_values: List[str]) -> List[Dict[str, Any]]:
        """
        For each distinct sample value, suggest best (system, code, display) mapping if applicable.
        Returns list of {sourceValue, system, code, display, confidence}.
        """
        prompt = (
            "For each of the following clinical values, suggest a system+code+display if applicable. "
            "Use ICD-10-CM, LOINC, SNOMED CT, RxNorm when patterns match; otherwise return normalized text only. "
            "Respond JSON array of {sourceValue, system?, code?, display?, normalized?, confidence}.\n"
            f"Values: {sample_values[:50]}\nJSON only:"
        )
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            arr = json.loads(text)
            if not isinstance(arr, list):
                raise ValueError('Not an array')
            return arr
        except Exception as e:
            # Fallback to empty list; caller may blend with S-BERT
            return []
    
    def _fallback_prediction(self, csv_schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Fallback heuristic-based FHIR resource prediction
        
        Args:
            csv_schema: CSV schema
            
        Returns:
            Predicted resource
        """
        columns_lower = [c.lower() for c in csv_schema.keys()]
        
        # Define indicators with weights (domain-specific fields get higher weight)
        # Patient indicators (base weight: 1)
        patient_indicators = {
            'demographic': ['first_name', 'last_name', 'birth_date', 'date_of_birth', 'dob', 'gender', 'sex', 'race', 'ethnicity'],
            'identifier': ['mrn', 'patient_id', 'ssn', 'medical_record'],
            'contact': ['phone', 'email', 'address', 'zip']
        }
        
        # Condition indicators (weight: 3 for primary, 1 for secondary)
        condition_indicators = {
            'primary': ['diagnosis_code', 'diagnosis_description', 'condition_code', 'icd', 'icd10', 'icd_10'],
            'secondary': ['diagnosis', 'condition', 'disease', 'problem', 'onset', 'severity', 'clinical_status']
        }
        
        # Observation indicators (weight: 3 for primary, 1 for secondary)
        obs_indicators = {
            'primary': ['lab_code', 'lab_name', 'result_value', 'loinc', 'test_code'],
            'secondary': ['observation', 'measurement', 'result', 'value', 'test', 'lab', 'specimen']
        }
        
        # Medication indicators (weight: 3 for primary, 1 for secondary)
        med_indicators = {
            'primary': ['medication_code', 'drug_code', 'rxnorm', 'ndc'],
            'secondary': ['medication', 'drug', 'prescription', 'dosage', 'dose']
        }
        
        # Calculate weighted scores
        patient_score = 0
        patient_score += sum(3 for col in columns_lower if any(ind in col for ind in patient_indicators['demographic']))
        patient_score += sum(2 for col in columns_lower if any(ind in col for ind in patient_indicators['identifier']))
        patient_score += sum(1 for col in columns_lower if any(ind in col for ind in patient_indicators['contact']))
        
        condition_score = 0
        condition_score += sum(5 for col in columns_lower if any(ind in col for ind in condition_indicators['primary']))
        condition_score += sum(2 for col in columns_lower if any(ind in col for ind in condition_indicators['secondary']))
        
        obs_score = 0
        obs_score += sum(5 for col in columns_lower if any(ind in col for ind in obs_indicators['primary']))
        obs_score += sum(2 for col in columns_lower if any(ind in col for ind in obs_indicators['secondary']))
        
        med_score = 0
        med_score += sum(5 for col in columns_lower if any(ind in col for ind in med_indicators['primary']))
        med_score += sum(2 for col in columns_lower if any(ind in col for ind in med_indicators['secondary']))
        
        # Determine best match
        scores = {
            'Patient': patient_score,
            'Observation': obs_score,
            'Condition': condition_score,
            'MedicationRequest': med_score
        }
        
        predicted_resource = max(scores, key=scores.get)
        max_score = scores[predicted_resource]
        
        # Get key indicators for the predicted resource
        key_indicators = []
        if predicted_resource == 'Patient':
            all_patient_indicators = patient_indicators['demographic'] + patient_indicators['identifier']
            key_indicators = [c for c in csv_schema.keys() if any(ind in c.lower() for ind in all_patient_indicators)]
        elif predicted_resource == 'Condition':
            all_condition_indicators = condition_indicators['primary'] + condition_indicators['secondary']
            key_indicators = [c for c in csv_schema.keys() if any(ind in c.lower() for ind in all_condition_indicators)]
        elif predicted_resource == 'Observation':
            all_obs_indicators = obs_indicators['primary'] + obs_indicators['secondary']
            key_indicators = [c for c in csv_schema.keys() if any(ind in c.lower() for ind in all_obs_indicators)]
        elif predicted_resource == 'MedicationRequest':
            all_med_indicators = med_indicators['primary'] + med_indicators['secondary']
            key_indicators = [c for c in csv_schema.keys() if any(ind in c.lower() for ind in all_med_indicators)]
        
        # Calculate confidence based on score and uniqueness
        total_score = sum(scores.values())
        if total_score == 0:
            confidence = 0.5
        else:
            # Higher confidence if the winner is clearly ahead
            second_best_score = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
            score_margin = (max_score - second_best_score) / max_score if max_score > 0 else 0
            confidence = min(0.95, 0.6 + (score_margin * 0.35))
        
        return {
            "resource": predicted_resource,
            "confidence": confidence,
            "reasoning": f"Heuristic match based on {len(key_indicators)} matching column patterns",
            "key_indicators": key_indicators[:5]
        }


# Global Gemini AI instance
gemini_ai = None

def get_gemini_ai(api_key: str = None) -> GeminiAI:
    """Get or create Gemini AI singleton"""
    global gemini_ai
    if gemini_ai is None:
        gemini_ai = GeminiAI(api_key)
    return gemini_ai

