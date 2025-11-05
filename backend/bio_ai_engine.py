"""
Biomedical AI Engine using Sentence-BERT for Healthcare/EHR/HL7 Schema Mapping
Specialized for clinical terminology and semantic matching
"""
import os
import numpy as np
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer, util
from models import FieldMapping, TransformationType


class BiomedicalAIEngine:
    """
    AI Engine powered by Sentence-BERT with biomedical pre-training
    Optimized for EHR, HL7, and clinical data integration
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize the biomedical AI engine
        
        Args:
            model_name: Model to use. Defaults to biomedical-optimized model.
                       Options:
                       - 'dmis-lab/biobert-base-cased-v1.2' (BioBERT)
                       - 'emilyalsentzer/Bio_ClinicalBERT' (ClinicalBERT)
                       - 'pritamdeka/S-PubMedBert-MS-MARCO' (PubMedBERT for semantic search)
                       - 'sentence-transformers/all-MiniLM-L6-v2' (lightweight fallback)
        """
        # Default to a good semantic search model
        # For production, use a fine-tuned biomedical model
        self.model_name = model_name or "sentence-transformers/all-MiniLM-L6-v2"
        
        print(f"🔬 Loading Sentence-BERT model: {self.model_name}")
        print("⏳ This may take a minute on first run (downloading model)...")
        
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"✅ Model loaded successfully!")
        except Exception as e:
            print(f"⚠️  Error loading model {self.model_name}: {e}")
            print("📦 Falling back to lightweight model...")
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Clinical terminology patterns for enhanced matching
        self.clinical_patterns = {
            'patient': ['patient', 'pt', 'subject', 'individual', 'person'],
            'name': ['name', 'full_name', 'fullname', 'patient_name', 'given_name', 'family_name'],
            'identifier': ['id', 'identifier', 'mrn', 'patient_id', 'medical_record_number', 'pid'],
            'date_of_birth': ['dob', 'date_of_birth', 'birth_date', 'birthdate', 'birth_dt'],
            'diagnosis': ['diagnosis', 'dx', 'condition', 'icd', 'problem', 'disease'],
            'medication': ['medication', 'med', 'drug', 'prescription', 'rx', 'medicine'],
            'procedure': ['procedure', 'proc', 'cpt', 'operation', 'surgery', 'treatment'],
            'lab': ['lab', 'laboratory', 'test', 'loinc', 'result', 'observation'],
            'vital': ['vital', 'vitals', 'bp', 'hr', 'temp', 'temperature', 'blood_pressure'],
            'hl7_segment': ['pid', 'obx', 'obr', 'pv1', 'msh', 'nk1', 'dg1', 'pr1'],
        }
        
        # HL7 field structure patterns
        self.hl7_patterns = {
            'segment': r'([A-Z]{3})\-(\d+)',  # e.g., PID-5
            'component': r'([A-Z]{3})\-(\d+)\.(\d+)',  # e.g., PID-5.1
            'subcomponent': r'([A-Z]{3})\-(\d+)\.(\d+)\.(\d+)',  # e.g., PID-5.1.1
        }

        # Canonical enumerations for quick normalization
        self.fhir_admin_gender = ["male", "female", "other", "unknown"]
        self.common_boolean = ["true", "false", "yes", "no", "y", "n", "1", "0"]
    
    def analyze_schemas(
        self,
        source_schema: Dict[str, str],
        target_schema: Dict[str, str]
    ) -> List[FieldMapping]:
        """
        Analyze source and target schemas using Sentence-BERT embeddings
        
        Args:
            source_schema: Dictionary of source field names to types
            target_schema: Dictionary of target field names to types
            
        Returns:
            List of suggested field mappings with confidence scores
        """
        mappings = []
        
        # Generate embeddings for all fields
        source_fields = list(source_schema.keys())
        target_fields = list(target_schema.keys())
        
        # Enhance field names with type information for better semantic matching
        source_texts = [
            self._enhance_field_description(field, source_schema[field])
            for field in source_fields
        ]
        target_texts = [
            self._enhance_field_description(field, target_schema[field])
            for field in target_fields
        ]
        
        # Generate embeddings
        print(f"🧠 Generating embeddings for {len(source_fields)} source and {len(target_fields)} target fields...")
        source_embeddings = self.model.encode(source_texts, convert_to_tensor=True)
        target_embeddings = self.model.encode(target_texts, convert_to_tensor=True)
        
        # Calculate cosine similarity matrix
        similarity_matrix = util.cos_sim(source_embeddings, target_embeddings)
        
        # Convert to numpy for easier processing
        similarity_matrix = similarity_matrix.cpu().numpy()
        
        # Track which target fields have been mapped
        mapped_targets = set()
        
        # Find best mappings using semantic similarity
        for i, source_field in enumerate(source_fields):
            similarities = similarity_matrix[i]
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            target_field = target_fields[best_idx]
            
            # Only create mapping if confidence is above threshold
            # and target hasn't been mapped yet (for 1:1 mappings)
            if best_score > 0.3 and target_field not in mapped_targets:
                # Determine transformation type
                transform = self._suggest_transform(
                    source_field,
                    target_field,
                    source_schema[source_field],
                    target_schema[target_field]
                )
                
                mapping = FieldMapping(
                    sourceField=source_field,
                    targetField=target_field,
                    confidenceScore=round(float(best_score), 2),
                    suggestedTransform=transform,
                    transformParams=self._get_transform_params(source_field, target_field, transform)
                )
                
                mappings.append(mapping)
                mapped_targets.add(target_field)
        
        # Handle special patterns (name concatenation, HL7 field splitting, etc.)
        special_mappings = self._detect_special_patterns(source_schema, target_schema)
        for mapping in special_mappings:
            # Add if target field not already mapped
            if mapping.targetField not in mapped_targets:
                mappings.append(mapping)
                mapped_targets.add(mapping.targetField)
        
        # Sort by confidence score
        mappings.sort(key=lambda x: x.confidenceScore, reverse=True)
        
        print(f"✅ Generated {len(mappings)} mapping suggestions")
        return mappings
    
    def _enhance_field_description(self, field_name: str, field_type: str) -> str:
        """
        Enhance field name with type and context for better semantic matching
        
        Args:
            field_name: Field name
            field_type: Field data type
            
        Returns:
            Enhanced description string
        """
        # Convert snake_case and camelCase to readable format
        readable = field_name.replace('_', ' ').replace('-', ' ')
        
        # Add type information
        description = f"{readable} {field_type}"
        
        # Add clinical context if pattern matches
        for concept, patterns in self.clinical_patterns.items():
            if any(pattern in field_name.lower() for pattern in patterns):
                description += f" {concept} clinical data"
                break
        
        return description
    
    def _suggest_transform(
        self,
        source_field: str,
        target_field: str,
        source_type: str,
        target_type: str
    ) -> TransformationType:
        """Suggest transformation type based on field characteristics"""
        
        # Date/time transformations
        if 'date' in source_type.lower() or 'date' in target_type.lower():
            if source_type != target_type:
                return TransformationType.FORMAT_DATE
        
        # Check for HL7 field splitting (e.g., PID-5 -> PID-5.1, PID-5.2)
        if '-' in source_field and '.' in target_field:
            return TransformationType.SPLIT
        
        # String formatting
        if 'name' in source_field.lower() or 'name' in target_field.lower():
            if source_type == 'string' and target_type == 'string':
                # Could be TRIM, UPPERCASE, etc.
                return TransformationType.TRIM
        
        # Default to direct mapping
        return TransformationType.DIRECT
    
    def _get_transform_params(
        self,
        source_field: str,
        target_field: str,
        transform_type: TransformationType
    ) -> Dict[str, any]:
        """Get transformation parameters"""
        
        if transform_type == TransformationType.CONCAT:
            return {"separator": " "}
        elif transform_type == TransformationType.SPLIT:
            return {"separator": " ", "index": 0}
        elif transform_type == TransformationType.FORMAT_DATE:
            return {"source_format": "auto", "target_format": "YYYY-MM-DD"}
        
        return None
    
    def _detect_special_patterns(
        self,
        source_schema: Dict[str, str],
        target_schema: Dict[str, str]
    ) -> List[FieldMapping]:
        """
        Detect special mapping patterns like name concatenation
        
        Args:
            source_schema: Source schema
            target_schema: Target schema
            
        Returns:
            List of special pattern mappings
        """
        mappings = []
        
        # Convert to lowercase for pattern matching
        source_lower = {k.lower(): k for k in source_schema.keys()}
        target_lower = {k.lower(): k for k in target_schema.keys()}
        
        # Pattern 1: First name + Last name -> Full name
        first_name_key = self._find_field_pattern(source_lower, ['first_name', 'firstname', 'fname', 'given_name'])
        last_name_key = self._find_field_pattern(source_lower, ['last_name', 'lastname', 'lname', 'surname', 'family_name'])
        full_name_key = self._find_field_pattern(target_lower, ['full_name', 'fullname', 'name', 'patient_name'])
        
        if first_name_key and last_name_key and full_name_key:
            mappings.append(FieldMapping(
                sourceField=f"{source_lower[first_name_key]},{source_lower[last_name_key]}",
                targetField=target_lower[full_name_key],
                confidenceScore=0.95,
                suggestedTransform=TransformationType.CONCAT,
                transformParams={
                    "separator": " ",
                    "fields": [source_lower[first_name_key], source_lower[last_name_key]]
                }
            ))
        
        # Pattern 2: HL7 segment field combinations
        # e.g., PID-5.1 (last name) + PID-5.2 (first name) -> patient_name
        
        return mappings
    
    def _find_field_pattern(self, fields: Dict[str, str], patterns: List[str]) -> str:
        """Find field matching any of the patterns"""
        for pattern in patterns:
            if pattern in fields:
                return pattern
        return None

    # ------------------------------
    # Terminology helpers (S-BERT)
    # ------------------------------
    def normalize_by_similarity(self, value: str, domain: str = "admin-gender") -> Dict[str, str]:
        """Return a canonical normalization using semantic similarity within a domain."""
        text = str(value).strip()
        if domain == "admin-gender":
            candidates = self.fhir_admin_gender
        elif domain == "boolean":
            candidates = self.common_boolean
        else:
            candidates = []
        if not candidates:
            return {"normalized": text}
        try:
            emb_q = self.model.encode([text], convert_to_tensor=True)
            emb_c = self.model.encode(candidates, convert_to_tensor=True)
            sims = util.cos_sim(emb_q, emb_c)[0].cpu().numpy()
            idx = int(np.argmax(sims))
            score = float(sims[idx])
            norm = candidates[idx]
            # simple canonicalization for booleans
            if domain == "boolean":
                truthy = {"true", "yes", "y", "1"}
                norm = "true" if norm.lower() in truthy else "false"
            return {"normalized": norm, "confidence": round(score, 2)}
        except Exception:
            return {"normalized": text}

    def cluster_synonyms(self, values: List[str]) -> Dict[str, str]:
        """Cluster similar strings and select a centroid as canonical per cluster."""
        try:
            texts = [str(v) for v in values]
            _ = self.model.encode(texts, convert_to_tensor=True)
            # naive: pick exact string as canonical for now (placeholder)
            return {v: v for v in values}
        except Exception:
            return {v: v for v in values}


# Global AI engine instance
bio_ai_engine = None

def get_bio_ai_engine(model_name: str = None) -> BiomedicalAIEngine:
    """Get or create biomedical AI engine singleton"""
    global bio_ai_engine
    if bio_ai_engine is None:
        bio_ai_engine = BiomedicalAIEngine(model_name)
    return bio_ai_engine

