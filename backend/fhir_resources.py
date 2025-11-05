"""
FHIR Resource Schemas and Templates
Standardized FHIR R4 resource structures for MongoDB target
"""
from typing import Dict, Any


class FHIRResources:
    """FHIR R4 resource schemas and templates"""
    
    def __init__(self):
        self.resource_schemas = {
            'Patient': self._get_patient_schema(),
            'Observation': self._get_observation_schema(),
            'Condition': self._get_condition_schema(),
            'Procedure': self._get_procedure_schema(),
            'Encounter': self._get_encounter_schema(),
            'MedicationRequest': self._get_medication_request_schema(),
            'DiagnosticReport': self._get_diagnostic_report_schema()
        }
    
    def get_resource_schema(self, resource_type: str) -> Dict[str, str]:
        """
        Get FHIR resource schema
        
        Args:
            resource_type: FHIR resource type (Patient, Observation, etc.)
            
        Returns:
            Schema dictionary with FHIR paths and types
        """
        return self.resource_schemas.get(resource_type, {})
    
    def get_available_resources(self) -> list:
        """Get list of available FHIR resource types"""
        return list(self.resource_schemas.keys())
    
    def _get_patient_schema(self) -> Dict[str, str]:
        """FHIR Patient resource schema"""
        return {
            "resourceType": "string",
            "id": "string",
            "identifier[0].system": "string",
            "identifier[0].value": "string",
            "active": "boolean",
            "name[0].use": "string",
            "name[0].family": "string",
            "name[0].given[0]": "string",
            "name[0].given[1]": "string",
            "name[0].prefix[0]": "string",
            "name[0].suffix[0]": "string",
            "telecom[0].system": "string",
            "telecom[0].value": "string",
            "telecom[0].use": "string",
            "gender": "string",
            "birthDate": "date",
            "address[0].use": "string",
            "address[0].type": "string",
            "address[0].line[0]": "string",
            "address[0].city": "string",
            "address[0].state": "string",
            "address[0].postalCode": "string",
            "address[0].country": "string",
            "maritalStatus.coding[0].system": "string",
            "maritalStatus.coding[0].code": "string",
            "maritalStatus.text": "string",
            "contact[0].relationship[0].coding[0].code": "string",
            "contact[0].name.family": "string",
            "contact[0].name.given[0]": "string",
            "contact[0].telecom[0].value": "string"
        }
    
    def _get_observation_schema(self) -> Dict[str, str]:
        """FHIR Observation resource schema (for lab results, vitals)"""
        return {
            "resourceType": "string",
            "id": "string",
            "status": "string",
            "category[0].coding[0].system": "string",
            "category[0].coding[0].code": "string",
            "code.coding[0].system": "string",
            "code.coding[0].code": "string",
            "code.coding[0].display": "string",
            "code.text": "string",
            "subject.reference": "string",
            "effectiveDateTime": "datetime",
            "issued": "datetime",
            "valueQuantity.value": "decimal",
            "valueQuantity.unit": "string",
            "valueQuantity.system": "string",
            "valueQuantity.code": "string",
            "valueString": "string",
            "valueBoolean": "boolean",
            "interpretation[0].coding[0].code": "string",
            "interpretation[0].text": "string",
            "referenceRange[0].low.value": "decimal",
            "referenceRange[0].high.value": "decimal",
            "referenceRange[0].text": "string"
        }
    
    def _get_condition_schema(self) -> Dict[str, str]:
        """FHIR Condition resource schema (for diagnoses)"""
        return {
            "resourceType": "string",
            "id": "string",
            "clinicalStatus.coding[0].system": "string",
            "clinicalStatus.coding[0].code": "string",
            "verificationStatus.coding[0].code": "string",
            "category[0].coding[0].system": "string",
            "category[0].coding[0].code": "string",
            "severity.coding[0].code": "string",
            "code.coding[0].system": "string",
            "code.coding[0].code": "string",
            "code.coding[0].display": "string",
            "code.text": "string",
            "bodySite[0].coding[0].code": "string",
            "bodySite[0].text": "string",
            "subject.reference": "string",
            "onsetDateTime": "datetime",
            "recordedDate": "datetime",
            "stage[0].summary.coding[0].code": "string",
            "stage[0].summary.text": "string"
        }
    
    def _get_procedure_schema(self) -> Dict[str, str]:
        """FHIR Procedure resource schema"""
        return {
            "resourceType": "string",
            "id": "string",
            "status": "string",
            "category.coding[0].system": "string",
            "category.coding[0].code": "string",
            "code.coding[0].system": "string",
            "code.coding[0].code": "string",
            "code.coding[0].display": "string",
            "code.text": "string",
            "subject.reference": "string",
            "performedDateTime": "datetime",
            "performer[0].actor.reference": "string",
            "bodySite[0].coding[0].code": "string",
            "outcome.text": "string"
        }
    
    def _get_encounter_schema(self) -> Dict[str, str]:
        """FHIR Encounter resource schema"""
        return {
            "resourceType": "string",
            "id": "string",
            "status": "string",
            "class.system": "string",
            "class.code": "string",
            "type[0].coding[0].code": "string",
            "subject.reference": "string",
            "period.start": "datetime",
            "period.end": "datetime",
            "serviceProvider.reference": "string"
        }
    
    def _get_medication_request_schema(self) -> Dict[str, str]:
        """FHIR MedicationRequest resource schema"""
        return {
            "resourceType": "string",
            "id": "string",
            "status": "string",
            "intent": "string",
            "medicationCodeableConcept.coding[0].system": "string",
            "medicationCodeableConcept.coding[0].code": "string",
            "medicationCodeableConcept.text": "string",
            "subject.reference": "string",
            "authoredOn": "datetime",
            "requester.reference": "string",
            "dosageInstruction[0].text": "string",
            "dosageInstruction[0].timing.repeat.frequency": "integer",
            "dosageInstruction[0].doseAndRate[0].doseQuantity.value": "decimal",
            "dosageInstruction[0].doseAndRate[0].doseQuantity.unit": "string"
        }
    
    def _get_diagnostic_report_schema(self) -> Dict[str, str]:
        """FHIR DiagnosticReport resource schema"""
        return {
            "resourceType": "string",
            "id": "string",
            "status": "string",
            "category[0].coding[0].code": "string",
            "code.coding[0].system": "string",
            "code.coding[0].code": "string",
            "subject.reference": "string",
            "effectiveDateTime": "datetime",
            "issued": "datetime",
            "result[0].reference": "string",
            "conclusion": "string"
        }
    
    def create_fhir_resource_template(self, resource_type: str) -> Dict[str, Any]:
        """
        Create a FHIR resource template
        
        Args:
            resource_type: FHIR resource type
            
        Returns:
            Empty FHIR resource structure
        """
        templates = {
            'Patient': {
                "resourceType": "Patient",
                "id": "",
                "identifier": [],
                "active": True,
                "name": [{"use": "official", "family": "", "given": []}],
                "telecom": [],
                "gender": "",
                "birthDate": "",
                "address": []
            },
            'Observation': {
                "resourceType": "Observation",
                "id": "",
                "status": "final",
                "category": [],
                "code": {"coding": [], "text": ""},
                "subject": {"reference": ""},
                "effectiveDateTime": "",
                "valueQuantity": {"value": 0, "unit": "", "system": "", "code": ""},
                "referenceRange": []
            },
            'Condition': {
                "resourceType": "Condition",
                "id": "",
                "clinicalStatus": {"coding": []},
                "verificationStatus": {"coding": []},
                "category": [],
                "code": {"coding": [], "text": ""},
                "subject": {"reference": ""},
                "onsetDateTime": "",
                "recordedDate": ""
            }
        }
        
        return templates.get(resource_type, {"resourceType": resource_type})


# Global FHIR resources instance
fhir_resources = FHIRResources()

