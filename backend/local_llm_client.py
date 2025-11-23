"""
Local LLM Client
Supports OpenAI-compatible local LLM servers (e.g., LM Studio, Ollama, LocalAI)
"""
import os
import json
import requests
from typing import Dict, List, Any, Optional


class LocalLLMClient:
    """Client for OpenAI-compatible local LLM servers"""
    
    def __init__(self, base_url: str = None, model_name: str = None, timeout: int = 120):
        """
        Initialize Local LLM Client
        
        Args:
            base_url: Base URL of the local LLM server (e.g., http://127.0.0.1:1234)
            model_name: Model name to use (will auto-detect if not provided)
            timeout: Request timeout in seconds (default: 120s)
        """
        self.base_url = base_url or os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:1234")
        self.timeout = timeout
        self.model_name = model_name
        
        # Remove trailing slash from base_url
        self.base_url = self.base_url.rstrip('/')
        
        # Auto-detect model if not provided
        if not self.model_name:
            self.model_name = self._detect_model()
        
        print(f"[OK] Local LLM Client initialized: {self.base_url} (model: {self.model_name})")
    
    def _detect_model(self) -> str:
        """Auto-detect available model from the local LLM server"""
        # First, check if model name is set via environment variable
        env_model = os.getenv("LOCAL_LLM_MODEL_NAME")
        if env_model:
            print(f"[OK] Using model from env: {env_model}")
            return env_model
        
        # Otherwise, try to auto-detect
        try:
            response = requests.get(
                f"{self.base_url}/v1/models",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                model_id = data['data'][0].get('id', 'local-model')
                print(f"[OK] Auto-detected model: {model_id}")
                return model_id
            
        except Exception as e:
            print(f"[WARNING] Could not auto-detect model: {e}")
        
        # Default fallback
        return "openai/gpt-oss-20b"
    
    def is_available(self) -> bool:
        """Check if the local LLM server is available"""
        try:
            response = requests.get(
                f"{self.base_url}/v1/models",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def generate_content(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> Any:
        """
        Generate content using chat completions endpoint
        (Compatible with Gemini's generate_content interface)
        
        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
        
        Returns:
            Response object with .text attribute
        """
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract the generated text
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('message', {}).get('content', '')
                
                # Return an object with .text attribute to match Gemini interface
                class LocalLLMResponse:
                    def __init__(self, text):
                        self.text = text
                
                return LocalLLMResponse(content)
            
            raise ValueError("No content in response from local LLM")
            
        except requests.exceptions.Timeout:
            raise Exception(f"Local LLM request timed out after {self.timeout}s. The model might be processing a large request.")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Could not connect to local LLM server at {self.base_url}. Make sure the server is running.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Local LLM request failed: {str(e)}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Direct chat completion endpoint (OpenAI-compatible)
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text response
        """
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0].get('message', {}).get('content', '')
            
            raise ValueError("No content in response")
            
        except Exception as e:
            raise Exception(f"Chat completion failed: {str(e)}")
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        try:
            response = requests.get(
                f"{self.base_url}/v1/models",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except Exception as e:
            print(f"[WARNING] Could not fetch models: {e}")
            return []


# Singleton instance
_local_llm_client = None


def get_local_llm_client() -> LocalLLMClient:
    """Get or create singleton Local LLM Client instance"""
    global _local_llm_client
    if _local_llm_client is None:
        _local_llm_client = LocalLLMClient()
    return _local_llm_client

