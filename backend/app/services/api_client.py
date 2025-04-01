import os
import requests
import json
import logging
from app.core.config import settings

# Initialize logging
logger = logging.getLogger(__name__)

class LilypadClient:
    """Handles interaction with Lilypad API"""

    def __init__(self, api_token=None):
        self.api_url = settings.LILYPAD_API_URL
        self.api_token = api_token or os.getenv("LILYPAD_API_TOKEN") or settings.DEFAULT_LILYPAD_API_TOKEN

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
8. Summarize issues in a way that is natural and avoids referencing the original structure of the document."""

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
        return re.sub(r"\[CHUNK \d+.*?\]", "", context).strip()

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

        return "".join(full_response).strip() 