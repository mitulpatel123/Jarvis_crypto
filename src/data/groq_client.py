import os
import time
import logging
import json
from typing import List, Dict, Any, Optional
from groq import Groq, RateLimitError
from src.config.settings import settings

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self):
        self.api_keys = settings.GROQ_API_KEYS
        if not self.api_keys:
            logger.warning("No Groq API keys found in settings.")
        
        self.clients = [Groq(api_key=k) for k in self.api_keys]
        self.current_key_index = 0
        self.rate_limits = {i: {'remaining': 1000, 'reset': 0} for i in range(len(self.api_keys))}

    def _get_client(self):
        """Get the next available client based on rate limits."""
        start_index = self.current_key_index
        
        while True:
            # Check if current key is valid (simple check, can be more complex)
            limit_info = self.rate_limits[self.current_key_index]
            if limit_info['remaining'] > 0 or time.time() > limit_info['reset']:
                client = self.clients[self.current_key_index]
                # Update index for round-robin load balancing
                self.current_key_index = (self.current_key_index + 1) % len(self.clients)
                return client
            
            # Move to next key
            self.current_key_index = (self.current_key_index + 1) % len(self.clients)
            
            # If we've circled back to start, all keys are exhausted
            if self.current_key_index == start_index:
                logger.warning("All Groq API keys are rate limited. Waiting...")
                time.sleep(5) # Wait a bit and try again

    def _update_rate_limits(self, headers, key_index):
        """Update rate limit info from response headers."""
        try:
            remaining = int(headers.get('x-ratelimit-remaining-requests', 1000))
            reset_time = float(headers.get('x-ratelimit-reset-requests', 0))
            # Convert duration string (e.g., "12s") to timestamp if needed, 
            # but Groq usually sends duration or timestamp. 
            # Let's assume it might need parsing if it's not a float.
            # For now, we'll trust the header or default.
            
            # Actually Groq headers:
            # x-ratelimit-remaining-requests: 14
            # x-ratelimit-reset-requests: 2s
            
            if isinstance(reset_time, str):
                if 's' in reset_time:
                    reset_time = float(reset_time.replace('s', ''))
                elif 'm' in reset_time:
                    reset_time = float(reset_time.replace('m', '')) * 60
            
            self.rate_limits[key_index]['remaining'] = remaining
            self.rate_limits[key_index]['reset'] = time.time() + reset_time
            
        except Exception as e:
            logger.debug(f"Failed to parse rate limit headers: {e}")

    def query(self, 
              messages: List[Dict[str, str]], 
              model: str = "openai/gpt-oss-120b",
              tools: Optional[List[Dict]] = None,
              temperature: float = 0.7,
              **kwargs) -> Any:
        """
        Execute a query against the Groq API.
        """
        retries = 3
        while retries > 0:
            client = self._get_client()
            key_index = self.clients.index(client)

            try:
                params = {
                    "messages": messages,
                    "model": model,
                    "temperature": temperature,
                    **kwargs
                }
                if tools:
                    params["tools"] = tools
                    params["tool_choice"] = "auto"

                response = client.chat.completions.create(**params)
                return response.choices[0].message

            except RateLimitError as e:
                logger.warning(f"Rate limit hit for key {key_index}. Rotating...")
                self.rate_limits[key_index]['remaining'] = 0
                self.rate_limits[key_index]['reset'] = time.time() + 60 # Default wait
                retries -= 1
                
            except Exception as e:
                logger.error(f"Groq API Error: {e}")
                raise e
        
        raise Exception("Max retries exceeded for Groq API")

groq_client = GroqClient()
