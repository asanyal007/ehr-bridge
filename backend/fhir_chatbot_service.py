"""
FHIR Data Chatbot Service
Implements RAG (Retrieval-Augmented Generation) pattern for natural language querying of FHIR data
"""
import os
import json
import hashlib
import re
import time
import ast
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from mongodb_client import get_mongo_client


# Simplified FHIR Schema for LM Studio prompt
FHIR_SIMPLIFIED_SCHEMA = {
    "Patient": {
        "id": "string",
        "gender": "string (male, female, other, unknown)",
        "birthDate": "string (YYYY-MM-DD)",
        "name": [{"family": "string", "given": ["string"]}],
        "address": [{"city": "string", "state": "string", "country": "string"}],
        "identifier": [{"system": "string", "value": "string"}]
    },
    "Observation": {
        "id": "string",
        "subject": {"reference": "string (e.g., Patient/123)"},
        "code": {"coding": [{"system": "string", "code": "string", "display": "string"}]},
        "valueQuantity": {"value": "number", "unit": "string"},
        "effectiveDateTime": "string (ISO datetime)",
        "status": "string"
    },
    "Condition": {
        "id": "string",
        "subject": {"reference": "string"},
        "code": {"coding": [{"system": "string", "code": "string", "display": "string"}]},
        "onsetDateTime": "string",
        "clinicalStatus": {"text": "string"}
    },
    "MedicationRequest": {
        "id": "string",
        "subject": {"reference": "string"},
        "medicationCodeableConcept": {"coding": [{"system": "string", "code": "string", "display": "string"}]},
        "authoredOn": "string"
    },
    "DiagnosticReport": {
        "id": "string",
        "subject": {"reference": "string"},
        "code": {"coding": [{"system": "string", "code": "string", "display": "string"}]},
        "effectiveDateTime": "string",
        "status": "string"
    }
}


class QueryValidator:
    """Validates and sanitizes MongoDB queries"""
    
    ALLOWED_OPERATORS = [
        '$eq', '$ne', '$gt', '$gte', '$lt', '$lte', '$in', '$nin', '$regex', '$exists',
        '$and', '$or', '$nor', '$not', '$elemMatch', '$options'
    ]
    MAX_LIMIT = 1000
    
    @staticmethod
    def validate_query(query: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate MongoDB query structure
        
        Returns:
            (is_valid, error_message)
        """
        # Check required fields
        if 'resourceType' not in query:
            return False, "Missing resourceType"
        
        if query['resourceType'] not in ['Patient', 'Observation', 'Condition', 'MedicationRequest', 'DiagnosticReport']:
            return False, f"Invalid resourceType: {query['resourceType']}"
        
        # Validate filter
        if 'filter' in query:
            if not isinstance(query['filter'], dict):
                return False, "Filter must be a dictionary"
            
            # Check for dangerous operators
            if not QueryValidator._validate_filter_operators(query['filter']):
                return False, "Query contains disallowed operators"
        
        # Validate limit
        if 'limit' in query:
            if not isinstance(query['limit'], int) or query['limit'] < 1:
                return False, "Limit must be a positive integer"
            if query['limit'] > QueryValidator.MAX_LIMIT:
                query['limit'] = QueryValidator.MAX_LIMIT
        
        return True, ""
    
    @staticmethod
    def _validate_filter_operators(filter_obj: Dict, depth: int = 0) -> bool:
        """Recursively validate filter operators"""
        if depth > 5:  # Prevent deep nesting attacks
            return False
        
        for key, value in filter_obj.items():
            if key.startswith('$'):
                if key not in QueryValidator.ALLOWED_OPERATORS:
                    return False
            
            if isinstance(value, dict):
                if not QueryValidator._validate_filter_operators(value, depth + 1):
                    return False
        
        return True


class QueryCache:
    """Simple in-memory cache for query results"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.cache = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def _make_key(self, query: Dict[str, Any]) -> str:
        """Create cache key from query"""
        query_str = json.dumps(query, sort_keys=True)
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def get(self, query: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Get cached results if available and not expired"""
        key = self._make_key(query)
        if key in self.cache:
            cached_at, results = self.cache[key]
            age = (datetime.now() - cached_at).total_seconds()
            if age < self.ttl_seconds:
                print(f"[OK] Cache hit for query (age: {age:.1f}s)")
                return results
            else:
                # Expired
                del self.cache[key]
        return None
    
    def set(self, query: Dict[str, Any], results: List[Dict[str, Any]]):
        """Cache query results"""
        # Evict oldest if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
            del self.cache[oldest_key]
        
        key = self._make_key(query)
        self.cache[key] = (datetime.now(), results)
        print(f"[CACHE] Cached query results ({len(results)} records)")
    
    def clear(self):
        """Clear all cached results"""
        self.cache.clear()


class ChatbotAnalytics:
    """Track chatbot performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'cache_hits': 0,
            'avg_response_time': 0,
            'query_types': {}
        }
    
    def record_query(self, success: bool, response_time: float, resource_type: str):
        """Record query metrics"""
        self.metrics['total_queries'] += 1
        if success:
            self.metrics['successful_queries'] += 1
        else:
            self.metrics['failed_queries'] += 1
        
        # Update average response time
        n = self.metrics['total_queries']
        self.metrics['avg_response_time'] = (
            (self.metrics['avg_response_time'] * (n - 1) + response_time) / n
        )
        
        # Track query types
        if resource_type not in self.metrics['query_types']:
            self.metrics['query_types'][resource_type] = 0
        self.metrics['query_types'][resource_type] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        success_rate = 0
        if self.metrics['total_queries'] > 0:
            success_rate = (self.metrics['successful_queries'] / self.metrics['total_queries']) * 100
        
        return {
            **self.metrics,
            'success_rate': round(success_rate, 2)
        }


class FHIRChatbotService:
    """
    FHIR Data Chatbot using RAG pattern:
    1. Translation: Natural language → MongoDB query (via LM Studio)
    2. Retrieval: Execute query against MongoDB fhir_* collections
    3. Synthesis: Raw FHIR data → Plain English answer (via LM Studio)
    """
    
    def __init__(self, lm_studio_url: str = None, mongo_db: str = "ehr"):
        """
        Initialize FHIR Chatbot Service
        
        Args:
            lm_studio_url: LM Studio API base URL (default: http://127.0.0.1:1234)
            mongo_db: MongoDB database name for FHIR collections
        """
        self.lm_studio_url = lm_studio_url or os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234")
        self.mongo_db = mongo_db
        self.debug = os.getenv("FHIR_CHATBOT_DEBUG", "false").lower() in {"1", "true", "yes", "on"}
        
        # Ensure URL doesn't have trailing slash
        self.lm_studio_url = self.lm_studio_url.rstrip('/')
        
        # Get MongoDB client - use the underlying pymongo client directly
        # The MongoDBClient wrapper is for HL7 staging, but we need direct access
        from pymongo import MongoClient
        mongo_host = os.getenv("MONGO_HOST", "localhost")
        mongo_port = os.getenv("MONGO_PORT", "27017")
        connection_string = f"mongodb://{mongo_host}:{mongo_port}/"
        
        try:
            self.mongo_client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            # Test connection
            self.mongo_client.admin.command('ping')
            # Verify database exists and has collections
            db = self.mongo_client[self.mongo_db]
            collections = db.list_collection_names()
            print(f"[OK] FHIR Chatbot: MongoDB client connected, database: {self.mongo_db}, collections: {len(collections)}")
            if 'staging' in collections:
                staging_count = db['staging'].count_documents({})
                print(f"[OK] FHIR Chatbot: Found staging collection with {staging_count} records")
        except Exception as e:
            print(f"[ERROR] FHIR Chatbot: MongoDB connection failed: {e}")
            # Try to get client from wrapper as fallback
            mongo_client_wrapper = get_mongo_client()
            if mongo_client_wrapper and mongo_client_wrapper.client:
                self.mongo_client = mongo_client_wrapper.client
                print(f"[WARN] FHIR Chatbot: Using fallback MongoDB client from wrapper")
            else:
                self.mongo_client = None
                print(f"[ERROR] FHIR Chatbot: Could not initialize MongoDB client")
        
        # Initialize query cache
        self.query_cache = QueryCache(max_size=100, ttl_seconds=300)
        
        # Initialize analytics
        self.analytics = ChatbotAnalytics()
        
        print(f"[OK] FHIR Chatbot Service initialized with LM Studio at {self.lm_studio_url}")
    
    def _call_lm_studio(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        Call LM Studio chat completions endpoint
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Response text from LM Studio
        """
        url = f"{self.lm_studio_url}/v1/chat/completions"
        
        payload = {
            "model": "local-model",  # LM Studio uses this for local models
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract content from response
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                raise ValueError("No content in LM Studio response")
                
        except requests.exceptions.RequestException as e:
            self._debug(f"LM Studio API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self._debug(f"Response status: {e.response.status_code}")
                self._debug(f"Response body: {e.response.text}")
            raise Exception(f"LM Studio API error: {str(e)}")

    def _debug(self, message: str, payload: Any = None):
        """Helper to print debug logs when enabled."""
        if not self.debug:
            return
        print(f"[FHIRChatbot DEBUG] {message}")
        if payload is not None:
            try:
                print(json.dumps(payload, indent=2, default=str))
            except Exception:
                print(payload)

    def _strip_response_block(self, response_text: str) -> str:
        """Extract JSON-like payload from LM Studio response."""
        cleaned = response_text.strip()
        if '```json' in cleaned:
            cleaned = cleaned.split('```json', 1)[1]
            cleaned = cleaned.split('```', 1)[0]
        elif '```' in cleaned:
            cleaned = cleaned.split('```', 1)[1]
            cleaned = cleaned.split('```', 1)[0]

        if '{' in cleaned and '}' in cleaned:
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            cleaned = cleaned[start:end]

        return cleaned.strip()

    def _parse_model_query(self, response_text: str) -> Dict[str, Any]:
        """Parse LM Studio response into a dictionary with resiliency."""
        cleaned = self._strip_response_block(response_text or "")
        if not cleaned:
            raise ValueError("Empty response from model")

        self._debug("Cleaned LM Studio response", cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as primary_error:
            self._debug("Primary JSON decode failed", str(primary_error))

        # Attempt to remove trailing commas
        cleaned_no_trailing = re.sub(r',\s*(}\s*)', r'\1', cleaned)
        cleaned_no_trailing = re.sub(r',\s*(\]\s*)', r'\1', cleaned_no_trailing)
        try:
            return json.loads(cleaned_no_trailing)
        except json.JSONDecodeError as secondary_error:
            self._debug("Secondary JSON decode failed", str(secondary_error))

        python_like = re.sub(r'\btrue\b', 'True', cleaned_no_trailing, flags=re.IGNORECASE)
        python_like = re.sub(r'\bfalse\b', 'False', python_like, flags=re.IGNORECASE)
        python_like = re.sub(r'\bnull\b', 'None', python_like, flags=re.IGNORECASE)
        try:
            parsed = ast.literal_eval(python_like)
            if isinstance(parsed, (dict, list)):
                return parsed
        except Exception as literal_error:
            self._debug("literal_eval parsing failed", str(literal_error))

        raise ValueError("Unable to parse LM Studio response as JSON")

    def _sanitize_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure query has safe defaults and normalized structures."""
        if not isinstance(query, dict):
            raise ValueError("Model response is not a JSON object")

        sanitized = dict(query)

        resource_type = sanitized.get('resourceType')
        if resource_type not in FHIR_SIMPLIFIED_SCHEMA:
            self._debug("Invalid or missing resourceType, defaulting to Patient", resource_type)
            sanitized['resourceType'] = 'Patient'

        filter_obj = sanitized.get('filter', {})
        if filter_obj is None:
            filter_obj = {}
        elif isinstance(filter_obj, list):
            if all(isinstance(item, dict) for item in filter_obj):
                filter_obj = {'$and': filter_obj}
            else:
                self._debug("Filter list contains non-dict items; dropping filter", filter_obj)
                filter_obj = {}
        elif not isinstance(filter_obj, dict):
            self._debug("Filter is not a dict; clearing filter", filter_obj)
            filter_obj = {}
        sanitized['filter'] = filter_obj

        if 'count' in sanitized:
            count_val = sanitized['count']
            if isinstance(count_val, str):
                sanitized['count'] = count_val.strip().lower() in {"true", "1", "yes", "count", "y"}
            else:
                sanitized['count'] = bool(count_val)

        if sanitized.get('count'):
            sanitized.pop('limit', None)
        else:
            limit = sanitized.get('limit', 100)
            try:
                limit = int(limit)
            except (TypeError, ValueError):
                self._debug("Invalid limit value; defaulting to 100", limit)
                limit = 100
            sanitized['limit'] = max(1, min(limit, QueryValidator.MAX_LIMIT))

        return sanitized
    
    def get_sample_data(self, resource_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get sample data from a collection to help with empty result suggestions
        
        Args:
            resource_type: FHIR resource type
            limit: Number of sample records to return
        
        Returns:
            List of sample records
        """
        try:
            db = self.mongo_client[self.mongo_db]
            
            # Try staging collection first (primary source)
            if 'staging' in db.list_collection_names():
                collection = db['staging']
                cursor = collection.find({'resourceType': resource_type}).limit(limit)
                results = []
                for doc in cursor:
                    doc.pop('_id', None)
                    doc.pop('job_id', None)
                    doc.pop('ingested_at', None)
                    results.append(doc)
                if results:
                    return results
            
            # Fallback to fhir_* collection
            collection_name = f"fhir_{resource_type}"
            if collection_name in db.list_collection_names():
                collection = db[collection_name]
                cursor = collection.find({}).limit(limit)
                results = []
                for doc in cursor:
                    doc.pop('_id', None)
                    doc.pop('job_id', None)
                    doc.pop('persisted_at', None)
                    results.append(doc)
                return results
            
            return []
        except Exception as e:
            print(f"[WARN] Sample data error: {e}")
            return []
    
    def _plan_query_strategy(self, question: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Agentic Step 0: Plan the query strategy - analyze question complexity and determine approach
        
        Returns:
            Strategy dict with reasoning, complexity, and suggested approach
        """
        system_prompt = """You are a query planning agent. Analyze the user's question and determine:
1. What resource type(s) are needed
2. How complex the query is (simple, moderate, complex)
3. Whether it needs multi-step reasoning
4. What fields/filters are likely needed

Respond in JSON format:
{
    "resourceType": "Patient|Observation|Condition|MedicationRequest|DiagnosticReport|multiple",
    "complexity": "simple|moderate|complex",
    "needsMultiStep": true/false,
    "suggestedFields": ["field1", "field2"],
    "reasoning": "brief explanation of your analysis"
}"""

        context = ""
        if conversation_history:
            recent = conversation_history[-3:]
            context = "\n".join([
                f"Previous: {msg.get('content', '')[:100]}"
                for msg in recent if msg.get('role') == 'user'
            ])

        user_prompt = f"""Analyze this question: "{question}"
{('Context: ' + context) if context else ''}

Provide your analysis in JSON format."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self._call_lm_studio(messages, temperature=0.2, max_tokens=300)
            strategy = self._parse_model_query(response)
            self._debug("Query strategy", strategy)
            return strategy
        except Exception as e:
            self._debug(f"Planning failed, using default strategy: {e}")
            return {
                "resourceType": "Patient",
                "complexity": "simple",
                "needsMultiStep": False,
                "suggestedFields": [],
                "reasoning": "Default fallback"
            }

    def _validate_and_refine_query(self, query: Dict[str, Any], question: str, error_context: str = None) -> Tuple[Dict[str, Any], bool, str]:
        """
        Agentic validation: Check if query makes sense and refine if needed
        
        Returns:
            (refined_query, is_valid, error_message)
        """
        # First, check basic structure
        is_valid, error_msg = QueryValidator.validate_query(query)
        if not is_valid:
            return query, False, error_msg

        # If we have error context, try to refine
        if error_context:
            system_prompt = """You are a query refinement agent. A query failed with this error. 
Analyze the error and the original query, then provide a corrected query.

Rules:
1. Respond with ONLY valid JSON
2. Fix the specific issue mentioned in the error
3. Keep the original intent of the query
4. Ensure all field names match FHIR schema exactly"""

            user_prompt = f"""Original Question: {question}
Failed Query: {json.dumps(query, indent=2)}
Error: {error_context}

Provide a corrected query in JSON format."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            try:
                response = self._call_lm_studio(messages, temperature=0.3, max_tokens=500)
                refined = self._parse_model_query(response)
                refined = self._sanitize_query(refined)
                is_valid, error_msg = QueryValidator.validate_query(refined)
                if is_valid:
                    return refined, True, ""
                return refined, False, error_msg
            except Exception as e:
                self._debug(f"Refinement failed: {e}")
                return query, False, str(e)

        return query, True, ""

    def translate_to_query(self, question: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Agentic Step 1: Translate with planning, validation, and self-correction
        
        Args:
            question: User's natural language question
            conversation_history: Previous messages for context
        
        Returns:
            Query dict with validation status
        """
        # Step 1: Plan the query strategy
        strategy = self._plan_query_strategy(question, conversation_history)
        self._debug("Query strategy", strategy)

        max_retries = 4
        last_error = None
        last_query = None

        for attempt in range(max_retries):
            try:
                # Build context from conversation history
                context = ""
                if conversation_history:
                    recent = conversation_history[-5:]
                    context = "\n".join([
                        f"User: {msg['content']}" if msg['role'] == 'user' 
                        else f"Assistant: {msg['content']}"
                        for msg in recent
                    ])

                # Enhanced prompt with strategy awareness
                system_prompt = """You are an expert FHIR data query translator. Convert natural language questions into MongoDB queries.

IMPORTANT: Data is stored in MongoDB 'staging' collection with a 'resourceType' field. All queries will automatically filter by resourceType.

Available FHIR Resources and Fields:
""" + json.dumps(FHIR_SIMPLIFIED_SCHEMA, indent=2) + """

Rules:
1. Respond with ONLY valid JSON (no markdown, no explanation, no extra text)
2. Structure: {"resourceType": "Patient|Observation|Condition|MedicationRequest|DiagnosticReport", "filter": {}, "limit": number}
3. The 'filter' field will be applied to records in the 'staging' collection that have matching 'resourceType'
4. Use MongoDB dot notation for nested fields (e.g., "name.0.family": "Smith")
5. Use $regex for text search with case-insensitive flag (e.g., {"gender": {"$regex": "^male$", "$options": "i"}})
6. For partial matches, use: {"field": {"$regex": "value", "$options": "i"}}
7. For exact matches, use: {"field": "value"}
8. Default limit: 100 (max: 1000)
9. For counting, add "count": true
10. For date ranges, use $gte and $lte with ISO dates
11. For multiple conditions, use $and or $or
12. Be precise with field names - they must match FHIR schema exactly

Examples:
Q: "Show me female patients"
A: {"resourceType": "Patient", "filter": {"gender": "female"}, "limit": 100}

Q: "How many patients from Boston?"
A: {"resourceType": "Patient", "filter": {"address.0.city": {"$regex": "boston", "$options": "i"}}, "count": true}

Q: "Patients born after 1990"
A: {"resourceType": "Patient", "filter": {"birthDate": {"$gte": "1990-01-01"}}, "limit": 100}"""

                # Build messages for chat API
                messages = [
                    {"role": "system", "content": system_prompt}
                ]

                # Add strategy context if available
                if strategy.get('reasoning'):
                    messages.append({
                        "role": "system",
                        "content": f"Query Planning Analysis: {strategy.get('reasoning')}. Suggested resource type: {strategy.get('resourceType')}"
                    })

                # Add conversation history
                if conversation_history:
                    recent = conversation_history[-5:]
                    for msg in recent:
                        if msg.get('role') in ['user', 'assistant']:
                            messages.append({
                                "role": msg['role'],
                                "content": msg.get('content', '')
                            })

                # Add current question with error context if retrying
                user_message = question
                if attempt > 0 and last_error:
                    user_message = f"""Previous attempt failed: {last_error}
Original question: {question}
Please correct the query based on the error."""

                messages.append({"role": "user", "content": user_message})

                response_text = self._call_lm_studio(messages, temperature=0.2, max_tokens=1000)
                self._debug(f"LM Studio raw response (attempt {attempt + 1})", response_text)

                query_payload = self._parse_model_query(response_text)
                query = self._sanitize_query(query_payload)
                last_query = query

                # Validate and refine if needed
                query, is_valid, error_msg = self._validate_and_refine_query(
                    query, question, last_error if attempt > 0 else None
                )

                if not is_valid:
                    last_error = error_msg
                    self._debug(f"Query validation failed (attempt {attempt + 1}): {error_msg}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        # Last attempt - return with error but don't fail completely
                        query['error'] = error_msg
                        query['translation_error'] = error_msg
                        query['fallback'] = True
                        return query

                # Success!
                self._debug(f"Query translation successful on attempt {attempt + 1}")
                return query

            except Exception as e:
                last_error = str(e)
                self._debug(f"Query translation attempt {attempt + 1} failed: {last_error}")
                if attempt < max_retries - 1:
                    continue

        # All retries failed - return safe fallback with last query if available
        error_message = str(last_error) if last_error else "Unknown translation error"
        print(f"[ERROR] Query translation failed after {max_retries} attempts: {error_message}")
        
        fallback_query = last_query or {
            "resourceType": strategy.get('resourceType', 'Patient'),
            "filter": {},
            "limit": 100
        }
        fallback_query['error'] = f"Translation failed: {error_message}"
        fallback_query['translation_error'] = error_message
        fallback_query['fallback'] = True
        return fallback_query
    
    def _validate_results(self, results: List[Dict[str, Any]], query: Dict[str, Any], question: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Agentic validation: Check if results make sense for the question
        
        Returns:
            (is_valid, reason, alternative_query)
        """
        if not results:
            # Check if collection exists and has data
            resource_type = query.get('resourceType', 'Patient')
            try:
                db = self.mongo_client[self.mongo_db]
                
                # Check staging collection (primary source)
                staging_count = 0
                staging_has_resource_type = 0
                if 'staging' in db.list_collection_names():
                    staging_collection = db['staging']
                    staging_count = staging_collection.count_documents({})
                    staging_has_resource_type = staging_collection.count_documents({'resourceType': resource_type})
                
                # Check fhir_* collection (fallback)
                fhir_count = 0
                collection_name = f"fhir_{resource_type}"
                if collection_name in db.list_collection_names():
                    collection = db[collection_name]
                    fhir_count = collection.count_documents({})
                
                # Prioritize staging collection
                if staging_has_resource_type > 0:
                    return False, f"Query returned no results but {staging_has_resource_type} {resource_type} records exist in staging collection. Query might be too restrictive.", None
                elif staging_count > 0:
                    return False, f"No {resource_type} records in staging collection, but {staging_count} total records found. Data may have different resourceType.", None
                elif fhir_count > 0:
                    return False, f"Query returned no results but {fhir_count} {resource_type} records exist in fhir_{resource_type} collection. Query might be too restrictive.", None
                else:
                    return False, f"No {resource_type} records exist in database (checked staging and fhir_{resource_type} collections)", None
                    
            except Exception as e:
                import traceback
                self._debug(f"Collection check error: {e}\n{traceback.format_exc()}")
                return False, f"Collection check failed: {str(e)}", None
        
        # Results exist - validate they match the question intent
        if len(results) == 1 and 'count' in results[0]:
            return True, "Count query successful", None
        
        # For non-count queries, check if results seem relevant
        # This is a simple heuristic - could be enhanced
        return True, "Results found", None

    def _refine_query_for_empty_results(self, original_query: Dict[str, Any], question: str, sample_data: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        Agentic refinement: If query returned no results, try to create alternative query based on sample data
        """
        if not sample_data:
            return None

        system_prompt = """You are a query refinement agent. The original query returned no results, but sample data exists.
Analyze the sample data and the original question, then suggest a refined query that might work.

Rules:
1. Respond with ONLY valid JSON
2. Use fields that actually exist in the sample data
3. Make the query less restrictive (use $regex for partial matches, remove strict filters)
4. Keep the original intent"""

        user_prompt = f"""Original Question: {question}
Original Query: {json.dumps(original_query, indent=2)}
Sample Data Available: {json.dumps(sample_data[:3], indent=2)}

Suggest a refined query that uses fields from the sample data."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self._call_lm_studio(messages, temperature=0.4, max_tokens=500)
            refined = self._parse_model_query(response)
            refined = self._sanitize_query(refined)
            is_valid, _ = QueryValidator.validate_query(refined)
            if is_valid:
                return refined
        except Exception as e:
            self._debug(f"Query refinement failed: {e}")
        
        return None

    def execute_query(self, query: Dict[str, Any], question: str = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Agentic Step 2: Execute MongoDB query with validation and refinement
        
        Args:
            query: MongoDB query from translate_to_query()
            question: Original question for context (optional)
        
        Returns:
            (results, metadata) where metadata contains validation info
        """
        metadata = {
            "attempts": 1,
            "refined": False,
            "validation_passed": False
        }

        # Check cache first (skip for count queries)
        if not query.get('count', False):
            cached_results = self.query_cache.get(query)
            if cached_results is not None:
                metadata["cached"] = True
                return cached_results, metadata
        
        try:
            resource_type = query.get('resourceType', 'Patient')
            filter_obj = query.get('filter', {})
            limit = query.get('limit', 100)
            count_only = query.get('count', False)
            
            if not self.mongo_client:
                raise Exception("MongoDB client not initialized")
            
            db = self.mongo_client[self.mongo_db]
            
            # PRIMARY: Query staging collection (where ingestion writes FHIR data)
            # Add resourceType filter to staging query
            staging_filter = dict(filter_obj) if filter_obj else {}
            staging_filter['resourceType'] = resource_type
            
            # Check if staging collection exists
            try:
                collection_names = db.list_collection_names()
            except Exception as e:
                raise Exception(f"Failed to list MongoDB collections: {e}")
            
            if 'staging' in collection_names:
                collection = db['staging']
                self._debug(f"Querying staging collection for resourceType: {resource_type}")
                
                # Execute query on staging
                if count_only:
                    try:
                        # Debug: Log the exact filter being used
                        print(f"[DEBUG] Chatbot querying staging with filter: {staging_filter}")
                        count = collection.count_documents(staging_filter)
                        print(f"[DEBUG] Chatbot count query result: {count} documents in staging (resourceType={resource_type})")
                        self._debug(f"Count query result: {count} documents in staging (resourceType={resource_type})")
                        results = [{"count": count, "resourceType": resource_type}]
                    except Exception as e:
                        import traceback
                        error_trace = traceback.format_exc()
                        self._debug(f"Count query failed: {e}\n{error_trace}")
                        print(f"[ERROR] Chatbot count query failed: {e}")
                        print(f"[ERROR] Traceback: {error_trace}")
                        raise
                else:
                    cursor = collection.find(staging_filter).limit(limit)
                    results = []
                    for doc in cursor:
                        # Remove MongoDB _id field
                        if '_id' in doc:
                            doc.pop('_id', None)
                        # Remove internal ingestion fields
                        if 'job_id' in doc:
                            doc.pop('job_id', None)
                        if 'ingested_at' in doc:
                            doc.pop('ingested_at', None)
                        # Keep persisted_at if exists (from fhir store)
                        results.append(doc)
                    self._debug(f"Find query result: {len(results)} documents from staging (resourceType={resource_type})")
            else:
                # Fallback: Try fhir_* collection if staging doesn't exist
                collection_name = f"fhir_{resource_type}"
                self._debug(f"Staging collection not found, trying {collection_name} as fallback")
                
                if collection_name in db.list_collection_names():
                    collection = db[collection_name]
                    
                    if count_only:
                        count = collection.count_documents(filter_obj)
                        results = [{"count": count, "resourceType": resource_type}]
                    else:
                        cursor = collection.find(filter_obj).limit(limit)
                        results = []
                        for doc in cursor:
                            doc.pop('_id', None)
                            doc.pop('job_id', None)
                            doc.pop('persisted_at', None)
                            results.append(doc)
                else:
                    # No collection found
                    self._debug(f"Neither staging nor {collection_name} collection found")
                    results = []
            
            # Validate results
            is_valid, reason, alt_query = self._validate_results(results, query, question or "")
            metadata["validation_passed"] = is_valid
            metadata["validation_reason"] = reason

            # If no results and we have a question, try refinement
            if not results and question and not count_only:
                sample_data = self.get_sample_data(resource_type, 5)
                if sample_data:
                    refined_query = self._refine_query_for_empty_results(query, question, sample_data)
                    if refined_query:
                        metadata["refined"] = True
                        metadata["attempts"] = 2
                        self._debug("Trying refined query", refined_query)
                        
                        # Try refined query
                        filter_obj = refined_query.get('filter', {})
                        limit = refined_query.get('limit', 100)
                        cursor = collection.find(filter_obj).limit(limit)
                        results = []
                        for doc in cursor:
                            doc.pop('_id', None)
                            doc.pop('job_id', None)
                            doc.pop('persisted_at', None)
                            results.append(doc)
                        
                        metadata["refined_query"] = refined_query
                
                # Cache results if we got any
                if results:
                    self.query_cache.set(query, results)
            elif results:
                # Cache successful results
                self.query_cache.set(query, results)
            
            return results, metadata
        
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"[ERROR] Query execution error: {error_msg}")
            print(f"[ERROR] Traceback: {error_trace}")
            self._debug(f"Query execution error: {error_msg}\n{error_trace}")
            metadata["error"] = error_msg
            metadata["error_trace"] = error_trace
            return [], metadata
    
    def _describe_filters(self, filters: Dict[str, Any]) -> str:
        """Convert filter dict to human-readable description"""
        descriptions = []
        for key, value in filters.items():
            if isinstance(value, dict):
                if '$regex' in value:
                    descriptions.append(f"{key} containing '{value['$regex']}'")
                elif '$gte' in value:
                    descriptions.append(f"{key} >= {value['$gte']}")
                elif '$lte' in value:
                    descriptions.append(f"{key} <= {value['$lte']}")
                else:
                    descriptions.append(f"{key} = {value}")
            else:
                descriptions.append(f"{key} = '{value}'")
        return ", ".join(descriptions) if descriptions else "your criteria"
    
    def _extract_suggestions(self, sample_data: List[Dict], resource_type: str) -> List[str]:
        """Extract useful suggestions from sample data"""
        suggestions = []
        for record in sample_data:
            if resource_type == 'Patient':
                if 'gender' in record:
                    suggestions.append(f"gender = {record['gender']}")
                if 'address' in record and record['address']:
                    addr = record['address'][0] if isinstance(record['address'], list) else record['address']
                    if 'city' in addr:
                        suggestions.append(f"city = {addr['city']}")
        return list(set(suggestions))
    
    def _strip_markdown(self, text: str) -> str:
        """Remove markdown formatting from text"""
        # Remove bold/italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        # Remove links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Remove code blocks
        text = re.sub(r'`([^`]+)`', r'\1', text)
        return text
    
    def synthesize_answer(self, question: str, results: List[Dict[str, Any]], query: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """
        Agentic Step 3: Synthesize answer with context-aware reasoning
        
        Args:
            question: Original user question
            results: FHIR resources from execute_query()
            query: The MongoDB query that was used
            metadata: Execution metadata (validation info, refinement status, etc.)
        
        Returns:
            Plain English answer string
        """
        metadata = metadata or {}
        
        # Handle fallback queries with better explanation
        if query.get('fallback', False):
            error_reason = query.get('translation_error') or query.get('error') or "I couldn't interpret the request"
            
            # Try to provide helpful guidance based on error type
            if "resourceType" in error_reason.lower():
                guidance = "Please specify what type of data you're looking for: patients, observations, conditions, medications, or diagnostic reports."
            elif "field" in error_reason.lower() or "filter" in error_reason.lower():
                guidance = "The field name might not match the FHIR schema. Try rephrasing with common terms like 'gender', 'city', 'birth date', etc."
            else:
                guidance = "Try rephrasing with a clear resource and filter, for example: 'How many patients do we have?' or 'Show me female patients from Boston.'"
            
            return f"I had trouble understanding your question: {error_reason}. {guidance}"
        
        # Handle empty results with agentic reasoning
        if not results:
            resource_type = query.get('resourceType', 'records')
            filters = query.get('filter', {})
            
            # Check if query was refined
            if metadata.get('refined'):
                return f"I couldn't find any {resource_type} records matching your exact criteria, even after trying alternative approaches. The database might not have data matching those specific filters."
            
            if filters:
                filter_desc = self._describe_filters(filters)
                validation_reason = metadata.get('validation_reason', '')
                
                # Use validation reason if available
                if validation_reason and "records exist" in validation_reason:
                    # Get sample data to suggest alternatives
                    sample_data = self.get_sample_data(resource_type, 3)
                    if sample_data:
                        suggestions = self._extract_suggestions(sample_data, resource_type)
                        if suggestions:
                            return f"I couldn't find any {resource_type} records matching {filter_desc}, but I found other data in the database.\n\nTry searching with: {', '.join(suggestions[:3])}"
                
                return f"No {resource_type} records found matching {filter_desc}. Try different criteria or ask 'What {resource_type} data do we have?'"
            else:
                validation_reason = metadata.get('validation_reason', '')
                
                # Check if data might be in staging collection
                if validation_reason and "staging collection" in validation_reason:
                    return f"No {resource_type} records found in fhir_{resource_type} collection. {validation_reason}\n\nThis usually means the ingestion job wrote data to the staging collection but didn't transform it to FHIR format. Check if your ingestion job has mappings configured."
                
                if validation_reason:
                    return f"No {resource_type} records found. {validation_reason}"
                return f"No {resource_type} records found in the database. The collection might be empty."
        
        # Handle count queries
        if len(results) == 1 and 'count' in results[0]:
            count = results[0]['count']
            resource_type = results[0]['resourceType']
            return f"There are {count} {resource_type} records in the database."
        
        # Limit data sent to LM Studio
        sample_size = min(len(results), 10)
        sample_results = results[:sample_size]
        
        # Enhanced prompt with agentic reasoning
        system_prompt = """You are a clinical data assistant with reasoning capabilities. Answer the user's question in PLAIN TEXT ONLY (no markdown, no formatting).

Instructions:
1. Answer in plain, conversational English - NO MARKDOWN, NO ASTERISKS, NO FORMATTING
2. Be specific and accurate with numbers and facts
3. If showing counts, mention the total number of records
4. If showing patient data, respect privacy (use IDs, not full names)
5. Keep response concise (2-4 sentences max)
6. Use natural language, not technical jargon
7. DO NOT use any markdown formatting like **, __, [], (), etc.
8. If the query was refined or had issues, acknowledge that naturally in your response
9. Focus on answering what the user actually asked, not just describing the data"""

        # Add context about query execution
        context_note = ""
        if metadata.get('refined'):
            context_note = "\nNote: The original query returned no results, so I tried a refined approach and found these records."
        if metadata.get('validation_reason'):
            context_note += f"\nValidation: {metadata.get('validation_reason')}"

        user_prompt = f"""User Question: {question}

Query Used: {json.dumps(query, indent=2)}
{context_note}

FHIR Data (showing {sample_size} of {len(results)} records):
{json.dumps(sample_results, indent=2)}

Plain Text Answer:"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            answer = self._call_lm_studio(messages, temperature=0.7, max_tokens=500).strip()
            
            # Remove any markdown formatting that slipped through
            answer = self._strip_markdown(answer)
            
            # Add metadata footer if many results
            if len(results) > sample_size:
                answer += f"\n\n(Showing summary of {sample_size} out of {len(results)} total records)"
            
            return answer
            
        except Exception as e:
            print(f"[WARN] Answer synthesis error: {e}")
            # Fallback: basic summary in plain text
            resource_type = results[0].get('resourceType', 'records') if results else 'records'
            if results:
                return f"Found {len(results)} {resource_type} records matching your query."
            else:
                return "I couldn't generate a detailed answer, but I found the data you requested."
    
    def chat(self, question: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Agentic RAG pipeline with planning, validation, refinement, and self-correction
        
        Args:
            question: User's natural language question
            conversation_history: Previous conversation messages
        
        Returns:
            {
                "answer": "string",
                "query_used": {...},
                "results_count": int,
                "results_sample": [...],
                "response_time": float,
                "metadata": {...}
            }
        """
        start_time = time.time()
        success = False
        resource_type = "unknown"
        execution_metadata = {}
        
        try:
            # Agentic Step 1: Translate with planning and validation
            query = self.translate_to_query(question, conversation_history)
            resource_type = query.get('resourceType', 'unknown')
            execution_metadata['translation_attempts'] = query.get('_attempts', 1)

            # Agentic Step 2: Retrieve with validation and refinement
            if query.get('fallback', False):
                results = []
                execution_metadata['query_fallback'] = True
            else:
                results, exec_meta = self.execute_query(query, question)
                execution_metadata.update(exec_meta)
            
            # Agentic Step 3: Synthesize with context-aware reasoning
            answer = self.synthesize_answer(question, results, query, execution_metadata)
            
            success = True
            
            return {
                "answer": answer,
                "query_used": query,
                "results_count": len(results),
                "results_sample": results[:3] if results else [],
                "response_time": round(time.time() - start_time, 2),
                "translation_error": query.get('translation_error'),
                "did_fallback": query.get('fallback', False),
                "metadata": execution_metadata
            }
        
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"[ERROR] Chat pipeline error: {error_msg}")
            print(f"[ERROR] Full traceback: {error_trace}")
            
            # Include error details in metadata
            execution_metadata['error'] = error_msg
            execution_metadata['error_trace'] = error_trace
            
            # Try to provide helpful error message
            if "LM Studio" in error_msg or "connection" in error_msg.lower():
                answer = "I'm having trouble connecting to the language model. Please ensure LM Studio is running on http://127.0.0.1:1234 and try again."
            elif "timeout" in error_msg.lower():
                answer = "The request took too long to process. Please try rephrasing your question or ask something simpler."
            elif "MongoDB" in error_msg or "mongo" in error_msg.lower():
                answer = f"I encountered a database error: {error_msg}. Please check MongoDB connection and try again."
            else:
                # Include more detail for debugging
                answer = f"I encountered an error: {error_msg}. Please try rephrasing your question or ask something simpler."
            
            return {
                "answer": answer,
                "query_used": {},
                "results_count": 0,
                "results_sample": [],
                "error": error_msg,
                "response_time": round(time.time() - start_time, 2),
                "translation_error": error_msg,
                "did_fallback": False,
                "metadata": execution_metadata
            }
        
        finally:
            # Record metrics
            response_time = time.time() - start_time
            self.analytics.record_query(success, response_time, resource_type)


# Singleton instance
_chatbot_service = None


def get_chatbot_service(force_reload: bool = False) -> FHIRChatbotService:
    """Get or create singleton FHIR Chatbot Service instance
    
    Args:
        force_reload: If True, recreate the service instance (useful after code changes)
    """
    global _chatbot_service
    if _chatbot_service is None or force_reload:
        _chatbot_service = FHIRChatbotService()
    return _chatbot_service


def reset_chatbot_service():
    """Reset the chatbot service singleton (forces recreation on next get)"""
    global _chatbot_service
    _chatbot_service = None

