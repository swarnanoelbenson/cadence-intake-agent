"""
Step 2: Second Claude pass — verify the extraction against the original PDF.
Claude sees both the PDF and the extraction result and approves or flags it.
"""

import base64
import json
from pathlib import Path

import anthropic
from pydantic import BaseModel

from agents.classifier_extractor import ExtractionResult


class ReviewResult(BaseModel):
    approved: bool
    flags: list[str] = []
    notes: str


def run(
    pdf_path: Path,
    extraction: ExtractionResult,
    client: anthropic.Anthropic,
    config: dict,
    prompt_template: str,
) -> tuple[ReviewResult, anthropic.types.Usage]:
    pdf_data = base64.standard_b64encode(pdf_path.read_bytes()).decode("utf-8")

    # Embed the extraction JSON into the prompt template
    extraction_json = json.dumps(extraction.model_dump(), indent=2)
    prompt = prompt_template.replace("{EXTRACTION_JSON}", extraction_json)

    response = client.messages.create(
        model=config["model"],
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    text = next(b.text for b in response.content if b.type == "text")

    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {
            "approved": False,
            "flags": ["reviewer returned non-JSON response"],
            "notes": f"Parse error: {text[:100]}",
        }

    result = ReviewResult(**data)

    return result, response.usage
