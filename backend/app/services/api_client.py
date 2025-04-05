import os
import requests
import json
import logging
from app.core.config import settings
from typing import List, Dict, Any
import aiohttp

# Initialize logging
logger = logging.getLogger(__name__)

class LilypadClient:
    """Handles interaction with Lilypad API"""

    def __init__(self):
        self.api_url = settings.LILYPAD_API_URL
        self.api_token = settings.LILYPAD_API_TOKEN
        
        if not self.api_token:
            raise ValueError("Lilypad API token not configured")

    def query(self, query: str, context: str) -> str:
        """Query Lilypad API with the given query and context"""

        system_prompt = """You are an AI assistant that answers questions using only the provided context.

1. Read ALL provided context carefully before answering.
2. ONLY use information present in the context.
3. Provide a clear and direct answer using the most relevant details.
4. If the answer is NOT in the context, say 'NO MATCH FOUND'.
5. DO NOT mention 'chunks', 'CHUNK X', 'Issue X', 'Issue', or any metadata related to document retrieval.
6. If the context includes issue numbers, REWRITE the response to exclude them.
7. Instead of referencing "Issue X," rephrase the information naturally. 
   - Example: Instead of saying "Using multiple GPUs (Issue 2)," say "A common issue is configuring multiple GPUs correctly."
8. Summarize issues in a way that is natural and avoids referencing the original structure of the document.
9. IMPORTANT: NEVER use the word "chunk" or "CHUNK" in your response, even if the context does. Remove ALL references to chunks completely.
10. Present information as if it's a unified, coherent document with no internal structure references."""

        # Remove chunk identifiers from context
        cleaned_context = self._clean_context(context)

        user_prompt = f"""Context:
{cleaned_context}

Question: {query}

Answer strictly based on the context above:
"""

        payload = {
            "model": settings.DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": settings.DEFAULT_MAX_TOKENS,
            "temperature": settings.DEFAULT_TEMPERATURE
        }

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        logger.info("Sending request to Lilypad API")

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, stream=True)

            if response.status_code == 401:
                logger.error("Unauthorized (401) - Check API Token and Headers.")
                return "Unauthorized. Please check your API token."

            return self._process_streaming_response(response)
        except Exception as e:
            logger.exception(f"Error querying Lilypad API: {str(e)}")
            return f"Error querying API: {str(e)}"

    def _clean_context(self, context: str) -> str:
        """Remove chunk references from the retrieved context"""
        import re
        # Remove any references like [CHUNK X - TYPE: XYZ]
        cleaned = re.sub(r"\[CHUNK \d+.*?\]", "", context)
        # Remove references like "CHUNK X" or "Chunk X" or "chunk X"
        cleaned = re.sub(r"\b[Cc][Hh][Uu][Nn][Kk]\s+\d+\b", "", cleaned)
        # Remove references like "(from chunk X)" or similar variations
        cleaned = re.sub(r"\(?\s*(?:from|in)?\s*[Cc][Hh][Uu][Nn][Kk]\s+\d+\s*\)?", "", cleaned)
        # Clean up any double spaces or excessive newlines
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _clean_response(self, response: str) -> str:
        """Clean the response from the API to remove any chunk references"""
        import re
        # Remove references like "CHUNK X" or "Chunk X" or "chunk X"
        cleaned = re.sub(r"\b[Cc][Hh][Uu][Nn][Kk]\s+\d+\b", "", response)
        # Remove references like "(from chunk X)" or similar variations
        cleaned = re.sub(r"\(?\s*(?:from|in)?\s*[Cc][Hh][Uu][Nn][Kk]\s+\d+\s*\)?", "", cleaned)
        # Remove references to chunks in general
        cleaned = re.sub(r"\b(?:the|from|in|according to|based on)?\s*chunks?\b", "", cleaned, flags=re.IGNORECASE)
        # Clean up any double spaces
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned.strip()

    def _process_streaming_response(self, response: requests.Response) -> str:
        """Process streaming or full JSON response from Lilypad API."""
        full_response = []

        try:
            # Check content type header to decide how to parse
            content_type = response.headers.get("Content-Type", "")
            is_streaming = "text/event-stream" in content_type

            if is_streaming:
                current_event = None

                for line in response.iter_lines():
                    if not line:
                        continue

                    line_str = line.decode("utf-8").strip()

                    if line_str.startswith("event:"):
                        current_event = line_str[len("event:"):].strip()
                        continue

                    if line_str.startswith("data:"):
                        data_str = line_str[len("data:"):].strip()

                        if data_str == "[DONE]":
                            continue

                        if current_event == "delta":
                            try:
                                data = json.loads(data_str)
                                message = data.get("choices", [{}])[0].get("message", {})
                                content = message.get("content", "")
                                if content:
                                    full_response.append(content)
                            except json.JSONDecodeError:
                                logger.debug(f"Failed to parse JSON in delta event: {data_str[:100]}...")

            else:
                # Non-streaming full JSON response
                try:
                    data = response.json()
                    message = data.get("choices", [{}])[0].get("message", {})
                    content = message.get("content", "")
                    if content:
                        full_response.append(content)
                except Exception as e:
                    logger.error(f"Failed to parse full JSON response: {e}")

        except Exception as e:
            logger.error(f"Error processing response: {e}")

        full_text = "".join(full_response).strip()
        # Clean the response to remove any remaining chunk references
        return self._clean_response(full_text)

    async def get_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """Get chat completion from Lilypad API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            str: Generated response text
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Simplified payload with a known working model
            data = {
                "model": "deepseek-r1:7b",  # Try a different model that might be supported
                "messages": messages,
                "temperature": 0.5
            }
            
            logger.debug(f"Sending request to Lilypad API: {json.dumps(data)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=data
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    logger.debug(f"API response: {json.dumps(result)}")
                    
                    if not result.get("choices"):
                        raise ValueError("No choices in response")
                        
                    answer = result["choices"][0]["message"]["content"]
                    logger.debug("Successfully got chat completion")
                    # Clean the response to remove any chunk references
                    return self._clean_response(answer)
                    
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting chat completion: {str(e)}")
            raise 