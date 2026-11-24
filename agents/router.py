"""
Step 3: Move each PDF to its destination folder based on the review outcome.

Approved + confidence >= threshold  →  clients/<ClientName>/<doc_type>.pdf
Flagged or low confidence           →  needs_review/<original_filename>.pdf
"""

import shutil
from pathlib import Path

from agents.classifier_extractor import ExtractionResult
from agents.reviewer import ReviewResult


def route(
    pdf_path: Path,
    extraction: ExtractionResult,
    review: ReviewResult,
    config: dict,
) -> Path:
    threshold = config["confidence_threshold"]

    if review.approved and extraction.confidence >= threshold:
        # Sanitise the client name for use as a directory name
        client_slug = extraction.client_name.replace(" ", "_")
        dest_dir = Path("clients") / client_slug
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest = dest_dir / f"{extraction.doc_type}.pdf"
        shutil.copy2(pdf_path, dest)
        return dest

    else:
        dest_dir = Path("needs_review")
        dest_dir.mkdir(exist_ok=True)

        dest = dest_dir / pdf_path.name
        shutil.copy2(pdf_path, dest)
        return dest
