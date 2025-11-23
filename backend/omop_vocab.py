"""
OMOP Vocabulary Service for semantic concept matching and normalization.

This module provides services for mapping FHIR codes to OMOP Standard Concept IDs
using AI-powered semantic matching with confidence scoring and HITL review.
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import sqlite3
import pickle
import google.generativeai as genai
import os

from database import get_db_manager


@dataclass
class ConceptSuggestion:
    """Represents a concept mapping suggestion with confidence scoring"""
    concept_id: int
    concept_name: str
    vocabulary_id: str  # LOINC, SNOMED, ICD10CM, etc.
    domain_id: str
    standard_concept: str  # 'S' for standard
    confidence_score: float  # 0.0 to 1.0
    reasoning: str  # Why this concept was chosen
    alternatives: List['ConceptSuggestion']  # Top 3 alternatives
    source_code: str
    source_system: str


class OmopVocabularyService:
    """Service for OMOP vocabulary operations and concept lookups"""
    
    def __init__(self, db_path: str = "data/interop.db"):
        self.db_manager = get_db_manager(db_path)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyCwfd_DHnKMYOWMbqX5VVTmyRNBv-Ni5vI")
        
        # Configure Gemini
        genai.configure(api_key=self.gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        print("✅ OMOP Vocabulary Service initialized")
    
    def get_all_standard_concepts(
        self, 
        vocabulary_id: str = None,
        domain_id: str = None,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Get all standard concepts from OMOP vocabulary
        
        Args:
            vocabulary_id: Filter by vocabulary (LOINC, SNOMED, etc.)
            domain_id: Filter by domain (Condition, Measurement, etc.)
            limit: Maximum number of results
        
        Returns:
            List of concept dictionaries
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT concept_id, concept_name, vocabulary_id, domain_id, 
                       standard_concept, concept_code
                FROM concept 
                WHERE standard_concept = 'S'
            """
            params = []
            
            if vocabulary_id:
                query += " AND vocabulary_id = ?"
                params.append(vocabulary_id)
            
            if domain_id:
                query += " AND domain_id = ?"
                params.append(domain_id)
            
            query += " ORDER BY concept_id LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def search_concepts(
        self,
        query: str,
        vocabulary_id: str = None,
        domain_id: str = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search concepts by name or code
        
        Args:
            query: Search query
            vocabulary_id: Filter by vocabulary
            domain_id: Filter by domain
            limit: Maximum results
        
        Returns:
            List of matching concepts
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            sql_query = """
                SELECT concept_id, concept_name, vocabulary_id, domain_id, 
                       standard_concept, concept_code
                FROM concept 
                WHERE (concept_name LIKE ? OR concept_code LIKE ?)
                AND standard_concept = 'S'
            """
            params = [f"%{query}%", f"%{query}%"]
            
            if vocabulary_id:
                sql_query += " AND vocabulary_id = ?"
                params.append(vocabulary_id)
            
            if domain_id:
                sql_query += " AND domain_id = ?"
                params.append(domain_id)
            
            sql_query += " ORDER BY concept_id LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_concept_by_id(self, concept_id: int) -> Optional[Dict[str, Any]]:
        """Get concept by ID"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT concept_id, concept_name, vocabulary_id, domain_id, 
                       standard_concept, concept_code
                FROM concept 
                WHERE concept_id = ?
            """, (concept_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def normalize_values(
        self, 
        values: List[str], 
        domain: str, 
        vocabulary: str = None
    ) -> List[Dict[str, Any]]:
        """
        Normalize a list of values to OMOP concepts
        
        Args:
            values: List of values to normalize
            domain: OMOP domain (Gender, Condition, etc.)
            vocabulary: Optional vocabulary filter
        
        Returns:
            List of normalization suggestions
        """
        suggestions = []
        
        for value in values:
            try:
                # Use semantic matcher for normalization
                from omop_vocab import get_semantic_matcher
                matcher = get_semantic_matcher()
                
                # Create a mock FHIR coding for the value
                fhir_coding = {
                    'code': value,
                    'system': 'http://example.org/custom',
                    'display': value
                }
                
                # Get semantic suggestion
                suggestion = matcher.analyze_fhir_coding(fhir_coding, domain)
                
                suggestions.append({
                    'source_value': value,
                    'concept_id': suggestion.concept_id,
                    'concept_name': suggestion.concept_name,
                    'vocabulary_id': suggestion.vocabulary_id,
                    'confidence': suggestion.confidence_score,
                    'reasoning': suggestion.reasoning
                })
                
            except Exception as e:
                print(f"⚠️ Error normalizing value '{value}': {e}")
                # Add fallback suggestion
                suggestions.append({
                    'source_value': value,
                    'concept_id': 0,
                    'concept_name': f"Unknown {value}",
                    'vocabulary_id': 'Unknown',
                    'confidence': 0.0,
                    'reasoning': f"Error processing: {str(e)}"
                })
        
        return suggestions
    
    def store_embedding(
        self,
        concept_id: int,
        concept_name: str,
        vocabulary_id: str,
        domain_id: str,
        embedding: np.ndarray,
        standard_concept: str = None
    ):
        """Store concept embedding"""
        embedding_bytes = pickle.dumps(embedding)
        self.db_manager.store_concept_embedding(
            concept_id=concept_id,
            concept_name=concept_name,
            vocabulary_id=vocabulary_id,
            domain_id=domain_id,
            embedding=embedding_bytes,
            standard_concept=standard_concept
        )
    
    def get_embeddings(
        self,
        vocabulary_id: str = None,
        domain_id: str = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get concept embeddings with optional filters"""
        return self.db_manager.get_concept_embeddings(
            vocabulary_id=vocabulary_id,
            domain_id=domain_id,
            limit=limit
        )


class OmopSemanticMatcher:
    """
    AI-powered semantic matcher for FHIR to OMOP concept mapping.
    
    Uses 4-stage matching (enhanced with GPT-OSS):
    1. Direct lookup in OMOP concept table
    2. GPT-OSS semantic embeddings (replaces S-BERT)
    3. GPT-OSS reasoning for ambiguous cases (enhanced)
    4. Fallback to Gemini AI if GPT-OSS unavailable
    """
    
    def __init__(self, db_path: str = "data/interop.db", use_gpt_oss: bool = True):
        self.vocab_service = OmopVocabularyService(db_path)
        self.db_manager = get_db_manager(db_path)
        
        # Initialize GPT-OSS client
        self.gpt_oss_client = None
        self.use_gpt_oss = use_gpt_oss
        
        if use_gpt_oss:
            try:
                from gpt_oss_client import get_gpt_oss_client
                self.gpt_oss_client = get_gpt_oss_client()
                if self.gpt_oss_client.is_available():
                    print("[OK] OMOP Semantic Matcher using GPT-OSS for enhanced matching")
                else:
                    print("[WARNING] GPT-OSS unavailable, falling back to traditional methods")
                    self.gpt_oss_client = None
            except Exception as e:
                print(f"[WARNING] GPT-OSS initialization failed: {e}")
                self.gpt_oss_client = None
        
        # Confidence thresholds
        self.CONFIDENCE_THRESHOLDS = {
            'auto_approve': 0.90,
            'review_required': 0.70,
            'reject': 0.50
        }
        
        print("[OK] OMOP Semantic Matcher initialized")
    
    def match_concept(
        self,
        source_code: str,
        source_system: str,
        source_display: str,
        target_domain: str,
        context: Dict = None
    ) -> ConceptSuggestion:
        """
        Match a source code to OMOP concept using 3-stage approach
        
        Args:
            source_code: Source code value
            source_system: Source code system (http://loinc.org, etc.)
            source_display: Source display text
            target_domain: Target OMOP domain
            context: Additional context (FHIR resource type, etc.)
        
        Returns:
            ConceptSuggestion with confidence score and alternatives
        """
        # Stage 1: Check cache first
        cached = self.db_manager.get_cached_concept_mapping(
            source_system=source_system,
            source_code=source_code,
            target_domain=target_domain
        )
        
        if cached and cached['confidence'] >= self.CONFIDENCE_THRESHOLDS['auto_approve']:
            concept = self.vocab_service.get_concept_by_id(cached['concept_id'])
            if concept:
                return ConceptSuggestion(
                    concept_id=concept['concept_id'],
                    concept_name=concept['concept_name'],
                    vocabulary_id=concept['vocabulary_id'],
                    domain_id=concept['domain_id'],
                    standard_concept=concept['standard_concept'],
                    confidence_score=cached['confidence'],
                    reasoning=cached.get('reasoning', 'Cached mapping'),
                    alternatives=[],
                    source_code=source_code,
                    source_system=source_system
                )
        
        # Stage 2: Direct lookup
        direct_match = self._direct_lookup(source_code, source_system, target_domain)
        if direct_match and direct_match.confidence_score >= 0.95:
            return direct_match
        
        # Stage 3: Semantic similarity (S-BERT simulation)
        semantic_matches = self._semantic_similarity(source_display, target_domain)
        if semantic_matches and semantic_matches[0].confidence_score >= 0.85:
            return semantic_matches[0]
        
        # Stage 4: AI reasoning (Gemini)
        ai_suggestion = self._ai_reasoning(
            source_code, source_system, source_display, 
            target_domain, context, semantic_matches
        )
        
        return ai_suggestion
    
    def _direct_lookup(
        self, 
        source_code: str, 
        source_system: str, 
        target_domain: str
    ) -> Optional[ConceptSuggestion]:
        """Stage 1: Direct lookup in OMOP concept table"""
        try:
            # Map FHIR system to OMOP vocabulary
            vocab_mapping = {
                'http://loinc.org': 'LOINC',
                'http://snomed.info/sct': 'SNOMED',
                'http://hl7.org/fhir/sid/icd-10-cm': 'ICD10CM',
                'http://www.nlm.nih.gov/research/umls/rxnorm': 'RxNorm'
            }
            
            vocabulary_id = vocab_mapping.get(source_system)
            if not vocabulary_id:
                return None
            
            # Search for exact code match
            concepts = self.vocab_service.search_concepts(
                query=source_code,
                vocabulary_id=vocabulary_id,
                domain_id=target_domain,
                limit=5
            )
            
            if concepts:
                concept = concepts[0]
                return ConceptSuggestion(
                    concept_id=concept['concept_id'],
                    concept_name=concept['concept_name'],
                    vocabulary_id=concept['vocabulary_id'],
                    domain_id=concept['domain_id'],
                    standard_concept=concept['standard_concept'],
                    confidence_score=0.95,  # High confidence for direct match
                    reasoning=f"Direct lookup: {source_code} → {concept['concept_name']}",
                    alternatives=[],
                    source_code=source_code,
                    source_system=source_system
                )
            
        except Exception as e:
            print(f"⚠️ Direct lookup error: {e}")
        
        return None
    
    def _semantic_similarity(
        self, 
        source_display: str, 
        target_domain: str
    ) -> List[ConceptSuggestion]:
        """Stage 2: GPT-OSS semantic similarity (enhanced from S-BERT)"""
        try:
            # Get candidate concepts from OMOP vocabulary
            concepts = self.vocab_service.search_concepts(
                query=source_display,
                domain_id=target_domain,
                limit=10  # Get more candidates for GPT-OSS ranking
            )
            
            if not concepts:
                return []
            
            suggestions = []
            
            # Use GPT-OSS embeddings for semantic matching
            if self.gpt_oss_client:
                try:
                    source_embedding = self.gpt_oss_client.get_embedding(source_display)
                    
                    # Calculate similarity for each candidate
                    scored_concepts = []
                    for concept in concepts:
                        concept_embedding = self.gpt_oss_client.get_embedding(concept['concept_name'])
                        similarity = self.gpt_oss_client.cosine_similarity(source_embedding, concept_embedding)
                        scored_concepts.append((concept, similarity))
                    
                    # Sort by similarity
                    scored_concepts.sort(key=lambda x: x[1], reverse=True)
                    
                    # Return top 5 with similarity scores
                    for concept, similarity in scored_concepts[:5]:
                        suggestion = ConceptSuggestion(
                            concept_id=concept['concept_id'],
                            concept_name=concept['concept_name'],
                            vocabulary_id=concept['vocabulary_id'],
                            domain_id=concept['domain_id'],
                            standard_concept=concept['standard_concept'],
                            confidence_score=round(similarity, 3),
                            reasoning=f"GPT-OSS semantic similarity: '{source_display}' → '{concept['concept_name']}' (score: {similarity:.3f})",
                            alternatives=[],
                            source_code="",
                            source_system=""
                        )
                        suggestions.append(suggestion)
                    
                    return suggestions
                    
                except Exception as e:
                    print(f"[WARNING] GPT-OSS similarity failed: {e}, falling back to simple scoring")
            
            # Fallback: simple position-based scoring
            for i, concept in enumerate(concepts[:5]):
                confidence = max(0.6, 0.9 - (i * 0.1))
                
                suggestion = ConceptSuggestion(
                    concept_id=concept['concept_id'],
                    concept_name=concept['concept_name'],
                    vocabulary_id=concept['vocabulary_id'],
                    domain_id=concept['domain_id'],
                    standard_concept=concept['standard_concept'],
                    confidence_score=confidence,
                    reasoning=f"Text similarity: '{source_display}' → '{concept['concept_name']}'",
                    alternatives=[],
                    source_code="",
                    source_system=""
                )
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            print(f"[WARNING] Semantic similarity error: {e}")
            return []
    
    def _ai_reasoning(
        self,
        source_code: str,
        source_system: str,
        source_display: str,
        target_domain: str,
        context: Dict,
        semantic_matches: List[ConceptSuggestion]
    ) -> ConceptSuggestion:
        """Stage 3/4: AI reasoning with GPT-OSS (primary) or Gemini (fallback)"""
        try:
            # Prepare candidate concepts
            candidate_concepts = []
            if semantic_matches:
                for match in semantic_matches[:5]:  # Include top 5 for GPT-OSS
                    candidate_concepts.append({
                        'concept_id': match.concept_id,
                        'concept_name': match.concept_name,
                        'vocabulary_id': match.vocabulary_id,
                        'confidence': match.confidence_score
                    })
            
            # Try GPT-OSS first
            if self.gpt_oss_client:
                try:
                    return self._gpt_oss_reasoning(
                        source_code, source_system, source_display,
                        target_domain, context, candidate_concepts
                    )
                except Exception as e:
                    print(f"[WARNING] GPT-OSS reasoning failed: {e}, falling back to Gemini")
            
            # Fallback to Gemini
            return self._gemini_reasoning(
                source_code, source_system, source_display,
                target_domain, context, candidate_concepts
            )
            
        except Exception as e:
            print(f"[ERROR] AI reasoning failed: {e}")
            # Return first semantic match or empty suggestion
            if semantic_matches:
                return semantic_matches[0]
            else:
                return ConceptSuggestion(
                    concept_id=0,
                    concept_name="",
                    vocabulary_id="",
                    domain_id=target_domain,
                    standard_concept="",
                    confidence_score=0.0,
                    reasoning=f"AI reasoning failed: {str(e)}",
                    alternatives=[],
                    source_code=source_code,
                    source_system=source_system
                )
    
    def _gpt_oss_reasoning(
        self,
        source_code: str,
        source_system: str,
        source_display: str,
        target_domain: str,
        context: Dict,
        candidate_concepts: List[Dict]
    ) -> ConceptSuggestion:
        """Enhanced reasoning using GPT-OSS"""
        # Build comprehensive prompt
        prompt = f"""You are an expert in clinical terminologies (LOINC, SNOMED, ICD-10, RxNorm) and the OMOP Common Data Model.

**Task**: Map a source clinical code to the most appropriate OMOP Standard Concept ID.

**Source Information**:
- Code System: {source_system}
- Code: {source_code}
- Display Text: {source_display}
- Target OMOP Domain: {target_domain}
- Clinical Context: {context or 'None provided'}

**Available OMOP Concept Candidates** (ranked by semantic similarity):
{json.dumps(candidate_concepts, indent=2)}

**Instructions**:
1. Analyze the clinical meaning and context of the source code
2. Consider the target domain requirements (e.g., Condition, Procedure, Drug, Measurement)
3. Evaluate each candidate concept for semantic accuracy and clinical appropriateness
4. Select the BEST matching OMOP concept ID, or 0 if no suitable match exists
5. Provide a confidence score (0.0 to 1.0) based on:
   - Semantic similarity (how well meanings align)
   - Domain appropriateness
   - Clinical context fit
   - Terminology standard alignment
6. Explain your reasoning in 2-3 concise sentences

**Important**: 
- Standard concepts are preferred (standard_concept = 'S')
- Higher semantic similarity candidates should be prioritized unless clinical context dictates otherwise
- Be conservative with confidence scores for ambiguous mappings

**Response Format** (JSON only, no markdown):
{{
  "concept_id": <selected_concept_id or 0>,
  "confidence": <0.0 to 1.0>,
  "reasoning": "<brief explanation>",
  "concerns": ["<any concerns or caveats>"]
}}
"""
        
        response = self.gpt_oss_client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical terminology mapping expert. Provide accurate, structured analysis for OMOP concept matching."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,  # Low temperature for consistent reasoning
            max_tokens=1000
        )
        
        # Parse JSON response
        response_text = response.strip()
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        result = json.loads(response_text)
        
        # Extract results
        concept_id = result.get('concept_id', 0)
        confidence = result.get('confidence', 0.0)
        reasoning = result.get('reasoning', 'GPT-OSS AI reasoning')
        concerns = result.get('concerns', [])
        
        if concept_id == 0:
            return ConceptSuggestion(
                concept_id=0,
                concept_name="No suitable match",
                vocabulary_id="",
                domain_id=target_domain,
                standard_concept="",
                confidence_score=confidence,
                reasoning=f"[GPT-OSS] {reasoning}",
                alternatives=candidate_concepts[:3] if candidate_concepts else [],
                source_code=source_code,
                source_system=source_system
            )
        
        # Get full concept details
        concept = self.vocab_service.get_concept_by_id(concept_id)
        if not concept:
            # Fallback to first candidate if concept not found
            if candidate_concepts:
                concept_id = candidate_concepts[0]['concept_id']
                concept = self.vocab_service.get_concept_by_id(concept_id)
        
        if concept:
            # Build alternatives list from other candidates
            alternatives = []
            for cand in candidate_concepts[:3]:
                if cand['concept_id'] != concept_id:
                    alternatives.append(cand)
            
            return ConceptSuggestion(
                concept_id=concept['concept_id'],
                concept_name=concept['concept_name'],
                vocabulary_id=concept['vocabulary_id'],
                domain_id=concept['domain_id'],
                standard_concept=concept['standard_concept'],
                confidence_score=confidence,
                reasoning=f"[GPT-OSS] {reasoning}" + (f" Concerns: {', '.join(concerns)}" if concerns else ""),
                alternatives=alternatives,
                source_code=source_code,
                source_system=source_system
            )
        else:
            return ConceptSuggestion(
                concept_id=concept_id,
                concept_name="Concept details unavailable",
                vocabulary_id="",
                domain_id=target_domain,
                standard_concept="",
                confidence_score=confidence,
                reasoning=f"[GPT-OSS] {reasoning}",
                alternatives=[],
                source_code=source_code,
                source_system=source_system
            )
    
    def _gemini_reasoning(
        self,
        source_code: str,
        source_system: str,
        source_display: str,
        target_domain: str,
        context: Dict,
        candidate_concepts: List[Dict]
    ) -> ConceptSuggestion:
        """Original Gemini AI reasoning (fallback)"""
        # Build prompt for Gemini
        prompt = f"""
You are an expert in clinical terminologies and OMOP Common Data Model.

Task: Map a source clinical code to the appropriate OMOP Standard Concept ID.

Source Information:
- Code System: {source_system}
- Code: {source_code}
- Display Text: {source_display}
- Target OMOP Domain: {target_domain}
- Clinical Context: {context or 'None'}

Available OMOP Concepts (Top candidates):
{json.dumps(candidate_concepts, indent=2)}

Instructions:
1. Analyze the semantic meaning of the source code
2. Consider the clinical context and target domain
3. Select the most appropriate OMOP Standard Concept ID
4. Provide confidence score (0.0 to 1.0)
5. Explain your reasoning in 1-2 sentences

If no suitable match is found, return concept_id: 0 with low confidence.

Respond in JSON:
{{
  "concept_id": 12345,
  "confidence": 0.92,
  "reasoning": "..."
}}
"""
        
        response = self.vocab_service.gemini_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Parse JSON response
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        result = json.loads(response_text)
        
        # Get concept details
        concept_id = result.get('concept_id', 0)
        confidence = result.get('confidence', 0.0)
        reasoning = result.get('reasoning', 'Gemini AI reasoning')
        
        if concept_id == 0:
            # No suitable match found
            return ConceptSuggestion(
                concept_id=0,
                concept_name="No Match Found",
                vocabulary_id="",
                domain_id=target_domain,
                standard_concept="",
                confidence_score=0.0,
                reasoning=f"[Gemini] {reasoning}",
                alternatives=candidate_concepts[:3] if candidate_concepts else [],
                source_code=source_code,
                source_system=source_system
            )
        
        # Get concept details
        concept = self.vocab_service.get_concept_by_id(concept_id)
        if not concept:
            return ConceptSuggestion(
                concept_id=0,
                concept_name="Invalid Concept ID",
                vocabulary_id="",
                domain_id=target_domain,
                standard_concept="",
                confidence_score=0.0,
                reasoning=f"[Gemini] Invalid concept ID returned: {concept_id}",
                alternatives=[],
                source_code=source_code,
                source_system=source_system
            )
        
        return ConceptSuggestion(
            concept_id=concept['concept_id'],
            concept_name=concept['concept_name'],
            vocabulary_id=concept['vocabulary_id'],
            domain_id=concept['domain_id'],
            standard_concept=concept['standard_concept'],
            confidence_score=confidence,
            reasoning=f"[Gemini] {reasoning}",
            alternatives=candidate_concepts[:3] if candidate_concepts else [],
            source_code=source_code,
            source_system=source_system
        )
    
    def analyze_fhir_coding(
        self,
        fhir_coding: Dict[str, Any],
        target_domain: str
    ) -> ConceptSuggestion:
        """
        Analyze complete FHIR coding element and return best match
        
        Args:
            fhir_coding: FHIR coding object
            target_domain: Target OMOP domain
        
        Returns:
            ConceptSuggestion with confidence and alternatives
        """
        source_code = fhir_coding.get('code', '')
        source_system = fhir_coding.get('system', '')
        source_display = fhir_coding.get('display', '')
        
        return self.match_concept(
            source_code=source_code,
            source_system=source_system,
            source_display=source_display,
            target_domain=target_domain,
            context={'fhir_coding': fhir_coding}
        )
    
    def validate_concept_mappings(
        self,
        job_id: str,
        auto_approve_threshold: float = 0.90
    ) -> Dict[str, Any]:
        """
        Validate all concept mappings for a job
        
        Args:
            job_id: Job ID
            auto_approve_threshold: Threshold for auto-approval
        
        Returns:
            Validation results with counts and review queue
        """
        # This would analyze all FHIR resources in the job
        # and determine which mappings need review
        
        # For now, return mock results
        return {
            "auto_approved": 0,
            "review_required": 0,
            "rejected": 0,
            "review_queue": []
        }


# Global instances
_vocab_service = None
_semantic_matcher = None

def get_vocab_service() -> OmopVocabularyService:
    """Get vocabulary service singleton"""
    global _vocab_service
    if _vocab_service is None:
        _vocab_service = OmopVocabularyService()
    return _vocab_service

def get_semantic_matcher() -> OmopSemanticMatcher:
    """Get semantic matcher singleton"""
    global _semantic_matcher
    if _semantic_matcher is None:
        _semantic_matcher = OmopSemanticMatcher()
    return _semantic_matcher