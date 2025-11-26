"""
Enhanced Biomedical AI Engine with GPT-OSS Integration
Replaces SENTENCE-BERT with GPT-OSS for improved semantic matching and reasoning
Falls back to SENTENCE-BERT if GPT-OSS is unavailable
"""
import os
import numpy as np
from typing import Dict, List, Tuple, Optional
from models import FieldMapping, TransformationType

# Try to import both GPT-OSS and SENTENCE-BERT
try:
    from gpt_oss_client import get_gpt_oss_client, MappingExplanation
    GPT_OSS_AVAILABLE = True
except ImportError:
    GPT_OSS_AVAILABLE = False
    print("[WARNING] GPT-OSS client not available")

try:
    from sentence_transformers import SentenceTransformer, util
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    print("[WARNING] SENTENCE-BERT not available")


class BiomedicalAIEngine:
    """
    Enhanced AI Engine with GPT-OSS for Healthcare/EHR/HL7 Schema Mapping
    - Primary: GPT-OSS (openai/gpt-oss-20b) for semantic similarity + reasoning
    - Fallback: SENTENCE-BERT for semantic similarity only
    """
    
    def __init__(self, use_gpt_oss: bool = True, sbert_model_name: str = None):
        """
        Initialize the biomedical AI engine
        
        Args:
            use_gpt_oss: Use GPT-OSS if available (default: True)
            sbert_model_name: SENTENCE-BERT model for fallback
        """
        self.use_gpt_oss = use_gpt_oss and GPT_OSS_AVAILABLE
        self.gpt_oss_client = None
        self.sbert_model = None
        
        # Try to initialize GPT-OSS first
        if self.use_gpt_oss:
            try:
                self.gpt_oss_client = get_gpt_oss_client()
                if self.gpt_oss_client.is_available():
                    print("[OK] Biomedical AI Engine using GPT-OSS for enhanced reasoning")
                    self.mode = "gpt_oss"
                else:
                    print("[WARNING] GPT-OSS server not available, falling back to SENTENCE-BERT")
                    self.gpt_oss_client = None
                    self.use_gpt_oss = False
            except Exception as e:
                print(f"[WARNING] GPT-OSS initialization failed: {e}")
                self.gpt_oss_client = None
                self.use_gpt_oss = False
        
        # Fall back to SENTENCE-BERT if GPT-OSS is not available
        if not self.use_gpt_oss and SBERT_AVAILABLE:
            self.model_name = sbert_model_name or "sentence-transformers/all-MiniLM-L6-v2"
            print(f"[OK] Loading SENTENCE-BERT model: {self.model_name}")
            
            try:
                self.sbert_model = SentenceTransformer(self.model_name)
                print("[OK] SENTENCE-BERT model loaded successfully")
                self.mode = "sbert"
            except Exception as e:
                print(f"[ERROR] Failed to load SENTENCE-BERT: {e}")
                raise RuntimeError("Neither GPT-OSS nor SENTENCE-BERT is available")
        
        if not self.gpt_oss_client and not self.sbert_model:
            raise RuntimeError("No embedding model available (GPT-OSS or SENTENCE-BERT)")
        
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
        
        # Canonical enumerations for quick normalization
        self.fhir_admin_gender = ["male", "female", "other", "unknown"]
        self.common_boolean = ["true", "false", "yes", "no", "y", "n", "1", "0"]
    
    def analyze_schemas(
        self,
        source_schema: Dict[str, str],
        target_schema: Dict[str, str],
        include_reasoning: bool = True
    ) -> List[FieldMapping]:
        """
        Analyze source and target schemas using GPT-OSS or SENTENCE-BERT
        
        Args:
            source_schema: Dictionary of source field names to types
            target_schema: Dictionary of target field names to types
            include_reasoning: Include GPT-OSS reasoning (only if GPT-OSS mode)
            
        Returns:
            List of suggested field mappings with confidence scores and reasoning
        """
        if self.mode == "gpt_oss":
            return self._analyze_with_gpt_oss(source_schema, target_schema, include_reasoning)
        else:
            return self._analyze_with_sbert(source_schema, target_schema)
    
    def _analyze_with_gpt_oss(
        self,
        source_schema: Dict[str, str],
        target_schema: Dict[str, str],
        include_reasoning: bool = True
    ) -> List[FieldMapping]:
        """Analyze schemas using GPT-OSS for embeddings + reasoning"""
        mappings = []
        
        source_fields = list(source_schema.keys())
        target_fields = list(target_schema.keys())
        
        print(f"[GPT-OSS] Analyzing {len(source_fields)} source fields -> {len(target_fields)} target fields")
        
        # Generate embeddings for all fields
        source_embeddings = {}
        target_embeddings = {}
        
        for field in source_fields:
            enhanced_text = self._enhance_field_description(field, source_schema[field])
            source_embeddings[field] = self.gpt_oss_client.get_embedding(enhanced_text)
        
        for field in target_fields:
            enhanced_text = self._enhance_field_description(field, target_schema[field])
            target_embeddings[field] = self.gpt_oss_client.get_embedding(enhanced_text)
        
        # Calculate similarity matrix
        mapped_targets = set()
        
        for source_field in source_fields:
            source_emb = source_embeddings[source_field]
            best_score = 0.0
            best_target = None
            
            for target_field in target_fields:
                if target_field in mapped_targets:
                    continue
                
                target_emb = target_embeddings[target_field]
                similarity = self.gpt_oss_client.cosine_similarity(source_emb, target_emb)
                
                if similarity > best_score:
                    best_score = similarity
                    best_target = target_field
            
            # Only create mapping if confidence is above threshold
            if best_score > 0.3 and best_target:
                # Get detailed explanation from GPT-OSS
                explanation = None
                if include_reasoning and best_score < 0.9:  # Only get explanation for uncertain mappings
                    try:
                        explanation = self.gpt_oss_client.explain_mapping(
                            source_field=source_field,
                            target_field=best_target,
                            source_type=source_schema[source_field],
                            target_type=target_schema[best_target]
                        )
                    except Exception as e:
                        print(f"[WARNING] Failed to get GPT-OSS explanation: {e}")
                
                # Determine transformation type
                transform = self._suggest_transform(
                    source_field,
                    best_target,
                    source_schema[source_field],
                    target_schema[best_target]
                )
                
                mapping = FieldMapping(
                    sourceField=source_field,
                    targetField=best_target,
                    confidenceScore=round(float(explanation.confidence if explanation else best_score), 2),
                    suggestedTransform=transform,
                    transformParams=self._get_transform_params(source_field, best_target, transform)
                )
                
                # Add GPT-OSS reasoning to mapping (as extra attributes)
                if explanation:
                    mapping.gpt_oss_reasoning = explanation.reasoning
                    mapping.gpt_oss_clinical_context = explanation.clinical_context
                    mapping.gpt_oss_type_compatible = explanation.type_compatibility
                
                mappings.append(mapping)
                mapped_targets.add(best_target)
        
        # Handle special patterns
        special_mappings = self._detect_special_patterns(source_schema, target_schema)
        for mapping in special_mappings:
            if mapping.targetField not in mapped_targets:
                mappings.append(mapping)
                mapped_targets.add(mapping.targetField)
        
        # Sort by confidence
        mappings.sort(key=lambda x: x.confidenceScore, reverse=True)
        
        print(f"[OK] Generated {len(mappings)} mapping suggestions with GPT-OSS")
        return mappings
    
    def _analyze_with_sbert(
        self,
        source_schema: Dict[str, str],
        target_schema: Dict[str, str]
    ) -> List[FieldMapping]:
        """Analyze schemas using SENTENCE-BERT (fallback mode)"""
        mappings = []
        
        source_fields = list(source_schema.keys())
        target_fields = list(target_schema.keys())
        
        # Enhance field names with type information
        source_texts = [
            self._enhance_field_description(field, source_schema[field])
            for field in source_fields
        ]
        target_texts = [
            self._enhance_field_description(field, target_schema[field])
            for field in target_fields
        ]
        
        # Generate embeddings
        print(f"[SBERT] Generating embeddings for {len(source_fields)} source and {len(target_fields)} target fields...")
        source_embeddings = self.sbert_model.encode(source_texts, convert_to_tensor=True)
        target_embeddings = self.sbert_model.encode(target_texts, convert_to_tensor=True)
        
        # Calculate cosine similarity matrix
        similarity_matrix = util.cos_sim(source_embeddings, target_embeddings)
        similarity_matrix = similarity_matrix.cpu().numpy()
        
        # Track mapped targets
        mapped_targets = set()
        
        # Find best mappings
        for i, source_field in enumerate(source_fields):
            similarities = similarity_matrix[i]
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            target_field = target_fields[best_idx]
            
            if best_score > 0.3 and target_field not in mapped_targets:
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
        
        # Handle special patterns
        special_mappings = self._detect_special_patterns(source_schema, target_schema)
        for mapping in special_mappings:
            if mapping.targetField not in mapped_targets:
                mappings.append(mapping)
                mapped_targets.add(mapping.targetField)
        
        mappings.sort(key=lambda x: x.confidenceScore, reverse=True)
        
        print(f"[OK] Generated {len(mappings)} mapping suggestions with SBERT")
        return mappings
    
    def _enhance_field_description(self, field_name: str, field_type: str) -> str:
        """Enhance field name with type and context for better semantic matching"""
        readable = field_name.replace('_', ' ').replace('-', ' ')
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
        
        # Check for HL7 field splitting
        if '-' in source_field and '.' in target_field:
            return TransformationType.SPLIT
        
        # String formatting
        if 'name' in source_field.lower() or 'name' in target_field.lower():
            if source_type == 'string' and target_type == 'string':
                return TransformationType.TRIM
        
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
        """Detect special mapping patterns like name concatenation"""
        mappings = []
        
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
        
        return mappings
    
    def _find_field_pattern(self, fields: Dict[str, str], patterns: List[str]) -> str:
        """Find field matching any of the patterns"""
        for pattern in patterns:
            if pattern in fields:
                return pattern
        return None
    
    def normalize_by_similarity(self, value: str, domain: str = "admin-gender") -> Dict[str, str]:
        """Return a canonical normalization using semantic similarity within a domain"""
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
            if self.mode == "gpt_oss":
                # Use GPT-OSS embeddings
                text_emb = self.gpt_oss_client.get_embedding(text)
                candidate_embs = [self.gpt_oss_client.get_embedding(c) for c in candidates]
                sims = [self.gpt_oss_client.cosine_similarity(text_emb, c_emb) for c_emb in candidate_embs]
                idx = int(np.argmax(sims))
                score = float(sims[idx])
            else:
                # Use SBERT
                emb_q = self.sbert_model.encode([text], convert_to_tensor=True)
                emb_c = self.sbert_model.encode(candidates, convert_to_tensor=True)
                sims = util.cos_sim(emb_q, emb_c)[0].cpu().numpy()
                idx = int(np.argmax(sims))
                score = float(sims[idx])
            
            norm = candidates[idx]
            
            # Simple canonicalization for booleans
            if domain == "boolean":
                truthy = {"true", "yes", "y", "1"}
                norm = "true" if norm.lower() in truthy else "false"
            
            return {"normalized": norm, "confidence": round(score, 2)}
            
        except Exception as e:
            print(f"[WARNING] Normalization failed: {e}")
            return {"normalized": text}


# Global AI engine instance
bio_ai_engine = None


def get_bio_ai_engine(use_gpt_oss: bool = True, sbert_model_name: str = None) -> BiomedicalAIEngine:
    """Get or create biomedical AI engine singleton"""
    global bio_ai_engine
    if bio_ai_engine is None:
        bio_ai_engine = BiomedicalAIEngine(use_gpt_oss=use_gpt_oss, sbert_model_name=sbert_model_name)
    return bio_ai_engine

