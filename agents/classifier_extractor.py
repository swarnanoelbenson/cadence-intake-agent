"""
Step 1: Send a PDF to Claude as a document block and extract structured data.
Returns a validated Pydantic model and the raw API usage stats for logging.
"""

import base64
import json
from pathlib import Path
from typing import Any

import anthropic
from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    client_name: str
    doc_type: str
    financial_year: str
    key_fields: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


def run(
    pdf_path: Path,
    client: anthropic.Anthropic,
    config: dict,
    prompt: str,
) -> tuple[ExtractionResult, anthropic.types.Usage]:
    # Encode the PDF as base64 — the Anthropic API accepts PDFs this way
    pdf_data = base64.standard_b64encode(pdf_path.read_bytes()).decode("utf-8")

    response = client.messages.create(
        model=config["model"],
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    # Document block: Claude reads the PDF directly
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    },
                    # Text block: the classification prompt
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    text = next(b.text for b in response.content if b.type == "text")

    # Strip markdown code fences if the model wrapped the JSON
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Fallback: if Claude returned non-JSON, treat as unknown with low confidence
        data = {
            "client_name": "unknown",
            "doc_type": "unknown",
            "financial_year": "unknown",
            "key_fields": {},
            "confidence": 0.1,
            "reasoning": f"Failed to parse model response as JSON: {text[:100]}",
        }

    # Validate with Pydantic — raises ValidationError if the schema is wrong
    result = ExtractionResult(**data)

    return result, response.usage
