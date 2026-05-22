"""
AI Classification Service - Azure OpenAI via Azure AI Foundry Responses API
Classifies expenses using a deployed Foundry model through the v1 Responses endpoint.
"""

import json
import re
from typing import Dict, Any

from backend.core.config import settings


def _build_v1_base_url(endpoint: str) -> str:
    """Normalize endpoint into OpenAI-compatible v1 base URL."""
    return endpoint.rstrip("/") + "/openai/v1/"


class AIClassificationService:
    """Service for expense classification using Azure AI Foundry Responses API."""

    @staticmethod
    async def classify_expense_ai(
        description: str,
        amount: float,
        category: str
    ) -> Dict[str, Any]:
        """
        Classify an expense using the configured Azure AI Foundry deployment.

        Args:
            description: Expense description
            amount: Expense amount
            category: Optional category hint

        Returns:
            Dict with classification, confidence, and reasoning
        """
        if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_API_KEY:
            return {
                "classification": "wants",
                "confidence": 0.3,
                "reasoning": "Azure OpenAI not configured. Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY."
            }

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                base_url=_build_v1_base_url(settings.AZURE_OPENAI_ENDPOINT)
            )

            system_message = """You are a personal finance assistant. Classify expenses into one of these categories:
- needs: Essential expenses (groceries, rent, utilities, healthcare, insurance, transportation to work)
- wants: Non-essential but desired items (entertainment, dining out, hobbies, luxury items)
- goals: Future-oriented savings or investments (retirement, emergency fund, down payment)

Respond with ONLY a JSON object in this exact format:
{"classification": "needs|wants|goals", "confidence": 0.0-1.0, "reasoning": "your explanation"}"""

            user_message = f"""Classify this expense:
Description: {description}
Amount: ${amount}
Category: {category or 'not specified'}"""

            # Use Foundry deployment through the OpenAI Responses API.
            response = await client.responses.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                input=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_output_tokens=300
            )

            response_text = (response.output_text or "").strip()

            try:
                json_match = re.search(r'\{[^{}]*"classification"[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    classification_data = json.loads(json_match.group(0))
                    return {
                        "classification": classification_data.get("classification", "wants"),
                        "confidence": float(classification_data.get("confidence", 0.7)),
                        "reasoning": classification_data.get("reasoning", "Classified by Azure AI Foundry")
                    }
            except (json.JSONDecodeError, ValueError):
                pass

            response_lower = response_text.lower()
            if "needs" in response_lower or "essential" in response_lower:
                classification = "needs"
            elif "goals" in response_lower or "savings" in response_lower or "investment" in response_lower:
                classification = "goals"
            else:
                classification = "wants"

            return {
                "classification": classification,
                "confidence": 0.6,
                "reasoning": response_text[:200]
            }

        except ImportError:
            return {
                "classification": "wants",
                "confidence": 0.3,
                "reasoning": "Azure OpenAI SDK not installed. Please add 'openai' to requirements.txt"
            }
        except Exception as e:
            print(f"Azure OpenAI error: {e}")
            return {
                "classification": "wants",
                "confidence": 0.3,
                "reasoning": f"Error calling Azure OpenAI: {str(e)}"
            }
