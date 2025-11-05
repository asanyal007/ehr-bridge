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
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import google.generativeai as genai
from mongodb_client import get_mongo_client


# Simplified FHIR Schema for Gemini prompt
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
                print(f"✅ Cache hit for query (age: {age:.1f}s)")
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
        print(f"💾 Cached query results ({len(results)} records)")
    
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
    1. Translation: Natural language → MongoDB query (via Gemini)
    2. Retrieval: Execute query against MongoDB fhir_* collections
    3. Synthesis: Raw FHIR data → Plain English answer (via Gemini)
    """
    
    def __init__(self, api_key: str = None, mongo_db: str = "ehr"):
        """
        Initialize FHIR Chatbot Service
        
        Args:
            api_key: Google Gemini API key
            mongo_db: MongoDB database name for FHIR collections
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "AIzaSyCwfd_DHnKMYOWMbqX5VVTmyRNBv-Ni5vI")
        self.mongo_db = mongo_db
        self.debug = os.getenv("FHIR_CHATBOT_DEBUG", "false").lower() in {"1", "true", "yes", "on"}
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Get MongoDB client
        self.mongo_client = get_mongo_client().client
        
        # Initialize query cache
        self.query_cache = QueryCache(max_size=100, ttl_seconds=300)
        
        # Initialize analytics
        self.analytics = ChatbotAnalytics()
        
        print(f"✅ FHIR Chatbot Service initialized with caching and analytics")

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
        """Extract JSON-like payload from Gemini response."""
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
        """Parse Gemini response into a dictionary with resiliency."""
        cleaned = self._strip_response_block(response_text or "")
        if not cleaned:
            raise ValueError("Empty response from model")

        self._debug("Cleaned Gemini response", cleaned)

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

        raise ValueError("Unable to parse Gemini response as JSON")

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
            collection_name = f"fhir_{resource_type}"
            db = self.mongo_client[self.mongo_db]
            collection = db[collection_name]
            
            cursor = collection.find({}).limit(limit)
            results = []
            for doc in cursor:
                # Remove MongoDB _id field
                doc.pop('_id', None)
                # Remove internal fields
                doc.pop('job_id', None)
                doc.pop('persisted_at', None)
                results.append(doc)
            
            return results
        except Exception as e:
            print(f"⚠️ Sample data error: {e}")
            return []
    
    def translate_to_query(self, question: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Step 1: Translate natural language question to MongoDB query using Gemini
        with validation and retry logic
        
        Args:
            question: User's natural language question
            conversation_history: Previous messages for context
        
        Returns:
            {
                "resourceType": "Patient",
                "filter": {"gender": "male"},
                "limit": 100
            }
        """
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Build context from conversation history
                context = ""
                if conversation_history:
                    recent = conversation_history[-5:]  # Increased from 3 to 5
                    context = "\n".join([
                        f"User: {msg['content']}" if msg['role'] == 'user' 
                        else f"Assistant: {msg['content']}"
                        for msg in recent
                    ])
                
                # Enhanced prompt with more examples
                prompt = f"""You are a FHIR data query translator. Convert natural language questions into MongoDB queries.

Available FHIR Resources and Fields:
{json.dumps(FHIR_SIMPLIFIED_SCHEMA, indent=2)}

Rules:
1. Respond with ONLY valid JSON (no markdown, no explanation, no extra text)
2. Structure: {{"resourceType": "Patient|Observation|Condition|MedicationRequest|DiagnosticReport", "filter": {{}}, "limit": number}}
3. Use MongoDB dot notation for nested fields (e.g., "name.0.family": "Smith")
4. Use $regex for text search with case-insensitive flag (e.g., {{"gender": {{"$regex": "^male$", "$options": "i"}}}})
5. For partial matches, use: {{"field": {{"$regex": "value", "$options": "i"}}}}
6. For exact matches, use: {{"field": "value"}}
7. Default limit: 100 (max: 1000)
8. For counting, add "count": true
9. For date ranges, use $gte and $lte with ISO dates
10. For multiple conditions, use $and or $or

Examples:
Q: "Show me female patients"
A: {{"resourceType": "Patient", "filter": {{"gender": "female"}}, "limit": 100}}

Q: "How many patients from Boston?"
A: {{"resourceType": "Patient", "filter": {{"address.0.city": {{"$regex": "boston", "$options": "i"}}}}, "count": true}}

Q: "Patients born after 1990"
A: {{"resourceType": "Patient", "filter": {{"birthDate": {{"$gte": "1990-01-01"}}}}, "limit": 100}}

{'Previous Context:' + chr(10) + context + chr(10) if context else ''}
User Question: {question}

MongoDB Query JSON:"""
                
                response = self.model.generate_content(prompt)
                response_text = response.text or ""
                self._debug(f"Gemini raw response (attempt {attempt + 1})", response_text)

                query_payload = self._parse_model_query(response_text)
                query = self._sanitize_query(query_payload)
                
                # Validate query
                is_valid, error_msg = QueryValidator.validate_query(query)
                if not is_valid:
                    raise ValueError(f"Invalid query: {error_msg}")
                
                # Success!
                return query
                
            except Exception as e:
                last_error = e
                self._debug(f"Query translation attempt {attempt + 1} failed", str(e))
                if attempt < max_retries - 1:
                    # Retry with simplified prompt
                    continue
        
        # All retries failed - return safe fallback
        error_message = str(last_error) if last_error else "Unknown translation error"
        print(f"❌ Query translation failed after {max_retries} attempts: {error_message}")
        return {
            "resourceType": "Patient",
            "filter": {},
            "limit": 100,
            "error": f"Translation failed: {error_message}",
            "translation_error": error_message,
            "fallback": True
        }
    
    def execute_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Step 2: Execute MongoDB query with caching
        
        Args:
            query: MongoDB query from translate_to_query()
        
        Returns:
            List of FHIR resources matching the query
        """
        # Check cache first (skip for count queries)
        if not query.get('count', False):
            cached_results = self.query_cache.get(query)
            if cached_results is not None:
                return cached_results
        
        try:
            resource_type = query.get('resourceType', 'Patient')
            filter_obj = query.get('filter', {})
            limit = query.get('limit', 100)
            count_only = query.get('count', False)
            
            # Get collection
            collection_name = f"fhir_{resource_type}"
            db = self.mongo_client[self.mongo_db]
            collection = db[collection_name]
            
            # Execute query
            if count_only:
                count = collection.count_documents(filter_obj)
                return [{"count": count, "resourceType": resource_type}]
            else:
                cursor = collection.find(filter_obj).limit(limit)
                results = []
                for doc in cursor:
                    # Remove MongoDB _id field
                    doc.pop('_id', None)
                    # Remove internal fields
                    doc.pop('job_id', None)
                    doc.pop('persisted_at', None)
                    results.append(doc)
                
                # Cache results
                if results:
                    self.query_cache.set(query, results)
                
                return results
        
        except Exception as e:
            print(f"⚠️ Query execution error: {e}")
            return []
    
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
    
    def synthesize_answer(self, question: str, results: List[Dict[str, Any]], query: Dict[str, Any]) -> str:
        """
        Step 3: Synthesize plain text answer with improved formatting
        
        Args:
            question: Original user question
            results: FHIR resources from execute_query()
            query: The MongoDB query that was used
        
        Returns:
            Plain English answer string
        """
        # Handle fallback queries
        if query.get('fallback', False):
            error_reason = query.get('translation_error') or query.get('error') or "I couldn't interpret the request"
            guidance = "Try rephrasing with a clear resource and filter, for example: 'How many patients do we have?' or 'Show me female patients from Boston.'"
            return f"I couldn't build a data query because: {error_reason}. {guidance}"
        
        # Handle empty results with better guidance
        if not results:
            resource_type = query.get('resourceType', 'records')
            filters = query.get('filter', {})
            
            if filters:
                filter_desc = self._describe_filters(filters)
                
                # Get sample data to suggest alternatives
                sample_data = self.get_sample_data(resource_type, 3)
                if sample_data:
                    suggestions = self._extract_suggestions(sample_data, resource_type)
                    if suggestions:
                        return f"I couldn't find any {resource_type} records matching {filter_desc}.\n\nTry searching for: {', '.join(suggestions[:3])}"
                
                return f"No {resource_type} records found matching {filter_desc}. Try different criteria or ask 'What {resource_type} data do we have?'"
            else:
                return f"No {resource_type} records found in the database. The collection might be empty."
        
        # Handle count queries
        if len(results) == 1 and 'count' in results[0]:
            count = results[0]['count']
            resource_type = results[0]['resourceType']
            return f"There are {count} {resource_type} records in the database."
        
        # Limit data sent to Gemini
        sample_size = min(len(results), 10)
        sample_results = results[:sample_size]
        
        # Enhanced prompt for plain text responses
        prompt = f"""You are a clinical data assistant. Answer the user's question in PLAIN TEXT ONLY (no markdown, no formatting).

User Question: {question}

Query Used: {json.dumps(query, indent=2)}

FHIR Data (showing {sample_size} of {len(results)} records):
{json.dumps(sample_results, indent=2)}

Instructions:
1. Answer in plain, conversational English - NO MARKDOWN, NO ASTERISKS, NO FORMATTING
2. Be specific and accurate with numbers and facts
3. If showing counts, mention the total ({len(results)} records)
4. If showing patient data, respect privacy (use IDs, not full names)
5. Keep response concise (2-4 sentences max)
6. Use natural language, not technical jargon
7. DO NOT use any markdown formatting like **, __, [], (), etc.

Plain Text Answer:"""
        
        try:
            response = self.model.generate_content(prompt)
            answer = response.text.strip()
            
            # Remove any markdown formatting that slipped through
            answer = self._strip_markdown(answer)
            
            # Add metadata footer if many results
            if len(results) > sample_size:
                answer += f"\n\n(Showing summary of {sample_size} out of {len(results)} total records)"
            
            return answer
            
        except Exception as e:
            print(f"⚠️ Answer synthesis error: {e}")
            # Fallback: basic summary in plain text
            resource_type = results[0].get('resourceType', 'records')
            return f"Found {len(results)} {resource_type} records matching your query."
    
    def chat(self, question: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Full RAG pipeline with timing and error tracking
        
        Args:
            question: User's natural language question
            conversation_history: Previous conversation messages
        
        Returns:
            {
                "answer": "string",
                "query_used": {...},
                "results_count": int,
                "results_sample": [...],
                "response_time": float
            }
        """
        start_time = time.time()
        success = False
        resource_type = "unknown"
        
        try:
            # Step 1: Translate
            query = self.translate_to_query(question, conversation_history)
            resource_type = query.get('resourceType', 'unknown')

            # Step 2: Retrieve (skip when fallback triggered)
            if query.get('fallback', False):
                results = []
            else:
                results = self.execute_query(query)
            
            # Step 3: Synthesize
            answer = self.synthesize_answer(question, results, query)
            
            success = True
            
            return {
                "answer": answer,
                "query_used": query,
                "results_count": len(results),
                "results_sample": results[:3] if results else [],
                "response_time": round(time.time() - start_time, 2),
                "translation_error": query.get('translation_error'),
                "did_fallback": query.get('fallback', False)
            }
        
        except Exception as e:
            print(f"❌ Chat pipeline error: {e}")
            return {
                "answer": f"I encountered an error processing your question: {str(e)}. Please try rephrasing or ask a simpler question.",
                "query_used": {},
                "results_count": 0,
                "results_sample": [],
                "error": str(e),
                "response_time": round(time.time() - start_time, 2),
                "translation_error": str(e),
                "did_fallback": False
            }
        
        finally:
            # Record metrics
            response_time = time.time() - start_time
            self.analytics.record_query(success, response_time, resource_type)


# Singleton instance
_chatbot_service = None


def get_chatbot_service() -> FHIRChatbotService:
    """Get or create singleton FHIR Chatbot Service instance"""
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = FHIRChatbotService()
    return _chatbot_service

