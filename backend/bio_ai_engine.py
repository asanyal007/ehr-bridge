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
    
    **Hybrid Mode** (Recommended):
    - SENTENCE-BERT for embeddings (fast, accurate)
    - GPT-OSS for reasoning (explanations, context)
    
    **GPT-OSS Only Mode**:
    - GPT-OSS for both embeddings and reasoning (slower)
    
    **SBERT Only Mode** (Fallback):
    - SENTENCE-BERT only (no reasoning)
    """
    
    def __init__(self, use_gpt_oss: bool = True, sbert_model_name: str = None):
        """
        Initialize the biomedical AI engine
        
        Args:
            use_gpt_oss: Use GPT-OSS for reasoning (default: True)
            sbert_model_name: SENTENCE-BERT model for embeddings
        """
        # Check if hybrid mode (SBERT embeddings + GPT-OSS reasoning)
        self.use_hybrid = os.getenv("USE_SBERT_EMBEDDINGS", "true").lower() == "true" and SBERT_AVAILABLE
        
        self.use_gpt_oss = use_gpt_oss and GPT_OSS_AVAILABLE
        self.gpt_oss_client = None
        self.sbert_model = None
        
        # Initialize SENTENCE-BERT for embeddings (hybrid or fallback mode)
        if self.use_hybrid or not self.use_gpt_oss:
            if SBERT_AVAILABLE:
                self.model_name = sbert_model_name or "sentence-transformers/all-MiniLM-L6-v2"
                print(f"[OK] Loading SENTENCE-BERT for embeddings: {self.model_name}")
                
                try:
                    self.sbert_model = SentenceTransformer(self.model_name)
                    print("[OK] SENTENCE-BERT loaded successfully")
                except Exception as e:
                    print(f"[WARNING] Failed to load SENTENCE-BERT: {e}")
                    if not self.use_gpt_oss:
                        raise RuntimeError("Neither GPT-OSS nor SENTENCE-BERT is available")
        
        # Initialize GPT-OSS for reasoning (hybrid or GPT-OSS only mode)
        if self.use_gpt_oss:
            try:
                self.gpt_oss_client = get_gpt_oss_client()
                if self.gpt_oss_client.is_available():
                    if self.use_hybrid and self.sbert_model:
                        print("[OK] Biomedical AI Engine in HYBRID mode:")
                        print("    - SENTENCE-BERT for embeddings (fast)")
                        print("    - GPT-OSS for reasoning (accurate)")
                        self.mode = "hybrid"
                    else:
                        print("[OK] Biomedical AI Engine using GPT-OSS")
                        self.mode = "gpt_oss"
                else:
                    print("[WARNING] GPT-OSS server not available")
                    self.gpt_oss_client = None
                    self.use_gpt_oss = False
                    if self.sbert_model:
                        self.mode = "sbert"
                    else:
                        raise RuntimeError("No AI engine available")
            except Exception as e:
                print(f"[WARNING] GPT-OSS initialization failed: {e}")
                self.gpt_oss_client = None
                self.use_gpt_oss = False
                if self.sbert_model:
                    self.mode = "sbert"
                else:
                    raise RuntimeError("No AI engine available")
        elif self.sbert_model:
            print("[OK] Biomedical AI Engine using SENTENCE-BERT only")
            self.mode = "sbert"
        else:
            raise RuntimeError("No AI engine available")
        
        if not self.gpt_oss_client and not self.sbert_model:
            raise RuntimeError("No embedding model available")
        
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
        Analyze source and target schemas
        
        Hybrid Mode: SBERT embeddings + GPT-OSS reasoning
        GPT-OSS Mode: GPT-OSS embeddings + reasoning
        SBERT Mode: SBERT embeddings only
        
        Args:
            source_schema: Dictionary of source field names to types
            target_schema: Dictionary of target field names to types
            include_reasoning: Include GPT-OSS reasoning (only if GPT-OSS available)
            
        Returns:
            List of suggested field mappings with confidence scores and reasoning
        """
        if self.mode == "hybrid":
            return self._analyze_hybrid(source_schema, target_schema, include_reasoning)
        elif self.mode == "gpt_oss":
            return self._analyze_with_gpt_oss(source_schema, target_schema, include_reasoning)
        else:
            return self._analyze_with_sbert(source_schema, target_schema)
    
    def _analyze_hybrid(
        self,
        source_schema: Dict[str, str],
        target_schema: Dict[str, str],
        include_reasoning: bool = True
    ) -> List[FieldMapping]:
        """
        Hybrid mode: SENTENCE-BERT embeddings + GPT-OSS reasoning
        
        This is the RECOMMENDED mode:
        - Fast embeddings from SBERT
        - Rich explanations from GPT-OSS
        """
        try:
            mappings = []
            
            source_fields = list(source_schema.keys())
            target_fields = list(target_schema.keys())
            
            # Extract target resource type for context
            target_resource_type = self._extract_resource_type(target_schema)
            
            print(f"[HYBRID] Analyzing {len(source_fields)} source → {len(target_fields)} target fields")
            if target_resource_type:
                print(f"[HYBRID] Target resource type: {target_resource_type}")
            print("[HYBRID] Using SBERT for embeddings + GPT-OSS for reasoning")
            
            # Verify GPT-OSS is available for low-confidence suggestions
            if include_reasoning:
                if self.gpt_oss_client and self.gpt_oss_client.is_available():
                    print("[HYBRID] GPT-OSS is available - AI suggestions will be generated for <40% confidence mappings")
                else:
                    print("[HYBRID WARNING] GPT-OSS not available - low-confidence suggestions may be limited")
                    if not self.gpt_oss_client:
                        print("[HYBRID WARNING] GPT-OSS client not initialized")
                    elif not self.gpt_oss_client.is_available():
                        print("[HYBRID WARNING] GPT-OSS server not responding - check if LM Studio is running")
            
            # Use SBERT for fast embedding generation
            source_texts = [
                self._enhance_field_description(field, source_schema[field])
                for field in source_fields
            ]
            target_texts = [
                self._enhance_field_description(field, target_schema[field])
                for field in target_fields
            ]
            
            print(f"[HYBRID] Generating SBERT embeddings...")
            source_embeddings = self.sbert_model.encode(source_texts, convert_to_tensor=True)
            target_embeddings = self.sbert_model.encode(target_texts, convert_to_tensor=True)
            
            similarity_matrix = util.cos_sim(source_embeddings, target_embeddings)
            similarity_matrix = similarity_matrix.cpu().numpy()
            
            mapped_targets = set()
            
            print(f"[HYBRID] Calculating similarities and generating mappings...")
            for i, source_field in enumerate(source_fields):
                try:
                    similarities = similarity_matrix[i]
                    best_idx = np.argmax(similarities)
                    best_score = float(similarities[best_idx])
                    target_field = target_fields[best_idx]
                    
                    if best_score > 0.3 and target_field not in mapped_targets:
                        # Get GPT-OSS explanation for uncertain mappings
                        explanation = None
                        low_conf_suggestion = None
                        
                        # CRITICAL: For low confidence mappings, ALWAYS generate AI suggestion immediately
                        if best_score < 0.4:
                            print(f"[AI] Low confidence detected ({best_score:.0%}): {source_field} -> {target_field}")
                            print(f"[AI] Generating AI suggestion NOW...")
                            
                            if include_reasoning and self.gpt_oss_client:
                                # Check availability first
                                if not self.gpt_oss_client.is_available():
                                    print(f"[AI WARNING] GPT-OSS server not available. Check if LM Studio is running on {self.gpt_oss_client.base_url}")
                                    low_conf_suggestion = {
                                        "action": "REVIEW",
                                        "suggestion": None,
                                        "reasoning": f"GPT-OSS server at {self.gpt_oss_client.base_url} is not available. Please ensure LM Studio is running with a model loaded. This field has very low confidence ({best_score:.0%}) mapping to '{target_field}'. Consider: 1) Mapping to Observation resource if this is a measurement, 2) Creating a custom extension, 3) Rejecting if not clinically relevant.",
                                        "alternative_resource": "Observation" if any(kw in source_field.lower() for kw in ['result', 'date', 'value', 'measurement']) else None
                                    }
                                else:
                                    try:
                                        # Generate AI suggestion synchronously - this MUST complete before creating mapping
                                        print(f"[AI] Calling GPT-OSS for {source_field}...")
                                        low_conf_suggestion = self.gpt_oss_client.suggest_action_for_low_confidence(
                                            source_field, 
                                            source_schema[source_field], 
                                            target_field, 
                                            best_score,
                                            target_resource_type=target_resource_type
                                        )
                                        print(f"[AI SUCCESS] Generated AI suggestion for {source_field}:")
                                        print(f"  Action: {low_conf_suggestion.get('action', 'UNKNOWN')}")
                                        print(f"  Reasoning: {low_conf_suggestion.get('reasoning', 'N/A')[:100]}...")
                                        if low_conf_suggestion.get('alternative_resource'):
                                            print(f"  Alternative Resource: {low_conf_suggestion.get('alternative_resource')}")
                                    except Exception as e:
                                        error_msg = str(e)
                                        print(f"[AI ERROR] Failed to generate suggestion for {source_field}: {error_msg}")
                                        
                                        # Provide helpful fallback based on error type
                                        if "Method Not Allowed" in error_msg or "405" in error_msg:
                                            fallback_reasoning = f"GPT-OSS API endpoint not available (Method Not Allowed). Please check LM Studio is running and supports OpenAI-compatible API at {self.gpt_oss_client.base_url}. This field '{source_field}' has very low confidence ({best_score:.0%}) mapping to '{target_field}'. Consider mapping to Observation resource or creating a custom extension."
                                        elif "Connection" in error_msg or "refused" in error_msg.lower():
                                            fallback_reasoning = f"Could not connect to GPT-OSS server. Please ensure LM Studio is running on {self.gpt_oss_client.base_url} with a model loaded. This field has very low confidence ({best_score:.0%})."
                                        else:
                                            fallback_reasoning = f"AI suggestion generation failed: {error_msg[:100]}. This field has very low confidence ({best_score:.0%}) mapping to '{target_field}'. Please review manually."
                                        
                                        low_conf_suggestion = {
                                            "action": "REVIEW",
                                            "suggestion": None,
                                            "reasoning": fallback_reasoning,
                                            "alternative_resource": "Observation" if any(kw in source_field.lower() for kw in ['result', 'date', 'value', 'measurement', 'test', 'lab']) else None
                                        }
                            else:
                                print(f"[AI WARNING] GPT-OSS not configured (include_reasoning={include_reasoning}, client={bool(self.gpt_oss_client)})")
                                low_conf_suggestion = {
                                    "action": "REVIEW",
                                    "suggestion": None,
                                    "reasoning": f"GPT-OSS not configured. This field has very low confidence ({best_score:.0%}). Please review manually.",
                                    "alternative_resource": None
                                }
                        
                        # Get explanation for uncertain mappings (but don't block on it)
                        if include_reasoning and self.gpt_oss_client and best_score < 0.9:
                            try:
                                print(f"[HYBRID] Getting GPT-OSS explanation for {source_field} -> {target_field}")
                                explanation = self.gpt_oss_client.explain_mapping(
                                    source_field=source_field,
                                    target_field=target_field,
                                    source_type=source_schema[source_field],
                                    target_type=target_schema[target_field]
                                )
                            except Exception as e:
                                print(f"[WARNING] GPT-OSS explanation failed for {source_field}->{target_field}: {e}")
                        
                        transform = self._suggest_transform(
                            source_field,
                            target_field,
                            source_schema[source_field],
                            target_schema[target_field]
                        )
                        
                        # Use explanation confidence if available, otherwise use similarity score
                        confidence = best_score
                        if explanation:
                            try:
                                confidence = float(explanation.confidence)
                            except (AttributeError, ValueError, TypeError):
                                pass  # Use best_score if explanation.confidence is invalid
                        
                        mapping = FieldMapping(
                            sourceField=source_field,
                            targetField=target_field,
                            confidenceScore=round(confidence, 2),
                            suggestedTransform=transform,
                            transformParams=self._get_transform_params(source_field, target_field, transform)
                        )
                        
                        # Add GPT-OSS reasoning (safely)
                        if explanation:
                            try:
                                mapping.gpt_oss_reasoning = explanation.reasoning if hasattr(explanation, 'reasoning') else None
                                mapping.gpt_oss_clinical_context = explanation.clinical_context if hasattr(explanation, 'clinical_context') else None
                                mapping.gpt_oss_type_compatible = explanation.type_compatibility if hasattr(explanation, 'type_compatibility') else None
                            except Exception as e:
                                print(f"[WARNING] Failed to add GPT-OSS attributes: {e}")
                        
                        # CRITICAL: Attach low-confidence suggestion (must be done for <40% mappings)
                        if best_score < 0.4:
                            if low_conf_suggestion:
                                mapping.low_confidence_suggestion = low_conf_suggestion
                                print(f"[VERIFY] Attached suggestion to mapping: {mapping.sourceField} has suggestion={bool(mapping.low_confidence_suggestion)}")
                            else:
                                print(f"[ERROR] No suggestion generated for {source_field} despite <40% confidence!")
                                # Force a fallback if somehow we don't have a suggestion
                                mapping.low_confidence_suggestion = {
                                    "action": "REVIEW",
                                    "suggestion": None,
                                    "reasoning": f"Field '{source_field}' has very low confidence ({best_score:.0%}) mapping to '{target_field}'. This may indicate: 1) Field should map to a different FHIR resource (e.g., Observation for measurements), 2) Field requires a custom extension, 3) Field should be ignored if not clinically relevant.",
                                    "alternative_resource": "Observation" if any(keyword in source_field.lower() for keyword in ['result', 'value', 'measurement', 'test', 'lab']) else None
                                }
                        
                        mappings.append(mapping)
                        mapped_targets.add(target_field)
                except Exception as e:
                    print(f"[ERROR] Failed to process mapping for {source_field}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Handle special patterns
            try:
                special_mappings = self._detect_special_patterns(source_schema, target_schema)
                for mapping in special_mappings:
                    if mapping.targetField not in mapped_targets:
                        mappings.append(mapping)
                        mapped_targets.add(mapping.targetField)
            except Exception as e:
                print(f"[WARNING] Special pattern detection failed: {e}")
            
            # Final pass: ALWAYS generate AI suggestions for low-confidence mappings (<40%)
            print("[HYBRID] Final pass: Generating AI suggestions for low-confidence mappings...")
            low_conf_count = 0
            for mapping in mappings:
                if mapping.confidenceScore < 0.4:
                    low_conf_count += 1
                    # Always regenerate suggestion to ensure we have the latest AI analysis
                    if include_reasoning and self.gpt_oss_client:
                        try:
                            # Find source type from schema
                            source_type = source_schema.get(mapping.sourceField, "unknown")
                            
                            print(f"[AI] Generating suggestion for {mapping.sourceField} -> {mapping.targetField} (confidence: {mapping.confidenceScore:.0%})")
                            suggestion = self.gpt_oss_client.suggest_action_for_low_confidence(
                                mapping.sourceField, 
                                source_type, 
                                mapping.targetField, 
                                mapping.confidenceScore,
                                target_resource_type=target_resource_type
                            )
                            mapping.low_confidence_suggestion = suggestion
                            print(f"[OK] AI suggestion generated for {mapping.sourceField}: {suggestion.get('action', 'UNKNOWN')}")
                        except Exception as e:
                            print(f"[ERROR] Failed to generate AI suggestion for {mapping.sourceField}: {e}")
                            import traceback
                            traceback.print_exc()
                            # Retry once with a simpler prompt
                            try:
                                print(f"[RETRY] Retrying AI suggestion for {mapping.sourceField}...")
                                suggestion = self.gpt_oss_client.suggest_action_for_low_confidence(
                                    mapping.sourceField, 
                                    source_type, 
                                    mapping.targetField, 
                                    mapping.confidenceScore,
                                    target_resource_type=target_resource_type
                                )
                                mapping.low_confidence_suggestion = suggestion
                                print(f"[OK] Retry successful for {mapping.sourceField}")
                            except Exception as e2:
                                print(f"[ERROR] Retry also failed for {mapping.sourceField}: {e2}")
                                # Only use fallback if GPT-OSS completely unavailable
                                if not self.gpt_oss_client.is_available():
                                    mapping.low_confidence_suggestion = {
                                        "action": "REVIEW",
                                        "suggestion": None,
                                        "reasoning": f"GPT-OSS server unavailable. Please review manually. This field ({mapping.sourceField}) has very low confidence ({mapping.confidenceScore:.0%}) mapping to {mapping.targetField}. Consider mapping to a different FHIR resource or creating a custom extension.",
                                        "alternative_resource": None
                                    }
                                else:
                                    # GPT-OSS is available but failed - still try to provide useful guidance
                                    mapping.low_confidence_suggestion = {
                                        "action": "REVIEW",
                                        "suggestion": None,
                                        "reasoning": f"AI analysis suggests reviewing this mapping. Field '{mapping.sourceField}' has very low confidence ({mapping.confidenceScore:.0%}) mapping to '{mapping.targetField}'. Consider: 1) Mapping to Observation resource if this is a measurement, 2) Creating a custom extension if source-specific, 3) Rejecting if not clinically relevant.",
                                        "alternative_resource": "Observation" if "date" in mapping.sourceField.lower() or "result" in mapping.sourceField.lower() else None
                                    }
                    else:
                        # GPT-OSS not available - provide basic guidance
                        if not self.gpt_oss_client:
                            mapping.low_confidence_suggestion = {
                                "action": "REVIEW",
                                "suggestion": None,
                                "reasoning": f"GPT-OSS not configured. This field has very low confidence ({mapping.confidenceScore:.0%}). Please review manually.",
                                "alternative_resource": None
                            }
            
            if low_conf_count > 0:
                print(f"[OK] Processed {low_conf_count} low-confidence mappings, generated AI suggestions")

            mappings.sort(key=lambda x: x.confidenceScore, reverse=True)
            
            print(f"[OK] Generated {len(mappings)} mappings (HYBRID mode: SBERT + GPT-OSS)")
            return mappings
            
        except Exception as e:
            print(f"[ERROR] Hybrid analysis failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to SBERT-only mode
            print("[FALLBACK] Attempting SBERT-only analysis...")
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
        
        # Extract target resource type for context
        target_resource_type = self._extract_resource_type(target_schema)
        
        print(f"[GPT-OSS] Analyzing {len(source_fields)} source fields -> {len(target_fields)} target fields")
        if target_resource_type:
            print(f"[GPT-OSS] Target resource type: {target_resource_type}")
        
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
                    low_conf_suggestion = None
                    
                    if include_reasoning:
                        if best_score < 0.4:
                             # Low confidence logic (<40%)
                             try:
                                 low_conf_suggestion = self.gpt_oss_client.suggest_action_for_low_confidence(
                                     source_field, source_schema[source_field], best_target, best_score,
                                     target_resource_type=target_resource_type
                                 )
                             except Exception as e:
                                 print(f"[WARNING] Low confidence suggestion failed: {e}")

                        if best_score < 0.9:  # Only get explanation for uncertain mappings
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
                
                if low_conf_suggestion:
                    mapping.low_confidence_suggestion = low_conf_suggestion

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
    
    def _extract_resource_type(self, target_schema: Dict[str, str]) -> Optional[str]:
        """
        Extract FHIR resource type from target schema paths
        
        Args:
            target_schema: Dictionary of target field paths (e.g., "Patient.name", "Observation.code")
            
        Returns:
            Resource type string (e.g., "Patient", "Observation") or None
        """
        if not target_schema:
            return None
        
        # Check first few target fields to find resource type
        for target_field in list(target_schema.keys())[:5]:
            # FHIR paths typically start with resource type (e.g., "Patient.name", "Observation.code")
            if '.' in target_field:
                resource_type = target_field.split('.')[0]
                # Validate it's a known FHIR resource type
                known_resources = ['Patient', 'Observation', 'Condition', 'Procedure', 
                                 'Encounter', 'MedicationRequest', 'DiagnosticReport',
                                 'Organization', 'Practitioner', 'Location']
                if resource_type in known_resources:
                    return resource_type
        
        return None
    
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

