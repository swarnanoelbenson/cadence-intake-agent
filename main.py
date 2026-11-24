"""
Cadence Intake Agent — main pipeline.
Run:  python main.py

For each PDF in inbox/:
  1. Classifier & Extractor  — Claude reads the PDF and extracts structured data
  2. Reviewer                — second Claude pass verifies the extraction
  3. Router                  — approved docs go to clients/, flagged to needs_review/
  4. Checklist               — per client: which required docs have we received?
  5. Drafter                 — for clients with gaps: draft a reminder email (never sent)

Every step is logged to logs/run.jsonl.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import yaml

from agents import classifier_extractor, reviewer, router, checklist, drafter


def load_prompt(name: str) -> str:
    return Path(f"prompts/{name}.md").read_text()


def append_log(log_file: Path, record: dict) -> None:
    with log_file.open("a") as f:
        f.write(json.dumps(record) + "\n")


def main() -> None:
    # ── Setup ───────────────────────────────────────────────────────────────
    config = yaml.safe_load(Path("config.yaml").read_text())
    api_client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment

    log_file = Path("logs/run.jsonl")
    log_file.parent.mkdir(exist_ok=True)

    classify_prompt = load_prompt("classifier_extractor")
    review_prompt = load_prompt("reviewer")
    draft_prompt = load_prompt("drafter")

    pdfs = sorted(Path("inbox").glob("*.pdf"))
    if not pdfs:
        print("No PDFs found in inbox/. Run:  python scripts/make_samples.py")
        return

    print(f"Processing {len(pdfs)} document(s)...\n")

    # client_name → list of approved doc_types (populated as we process each PDF)
    client_docs: dict[str, list[str]] = {}

    # ── Per-document pipeline ────────────────────────────────────────────────
    for pdf_path in pdfs:
        print(f"  [{pdf_path.name}]")
        t0 = time.time()

        # Step 1 — Classify and extract
        extraction, extract_usage = classifier_extractor.run(
            pdf_path, api_client, config, classify_prompt
        )
        print(
            f"    type={extraction.doc_type}  "
            f"client={extraction.client_name!r}  "
            f"conf={extraction.confidence:.2f}"
        )

        # Step 2 — Review
        review_result, review_usage = reviewer.run(
            pdf_path, extraction, api_client, config, review_prompt
        )
        status = "APPROVED" if review_result.approved else "FLAGGED"
        flags_str = ", ".join(review_result.flags) if review_result.flags else "none"
        print(f"    review={status}  flags={flags_str}")

        # Step 3 — Route
        dest = router.route(pdf_path, extraction, review_result, config)
        print(f"    → {dest}")

        # Track which docs we have per client (approved only)
        if review_result.approved and extraction.confidence >= config["confidence_threshold"]:
            bucket = client_docs.setdefault(extraction.client_name, [])
            bucket.append(extraction.doc_type)

        elapsed = round(time.time() - t0, 2)

        append_log(log_file, {
            "ts": datetime.now(timezone.utc).isoformat(),
            "step": "classify_review",
            "file": pdf_path.name,
            "client": extraction.client_name,
            "doc_type": extraction.doc_type,
            "financial_year": extraction.financial_year,
            "confidence": extraction.confidence,
            "reasoning": extraction.reasoning,
            "approved": review_result.approved,
            "flags": review_result.flags,
            "review_notes": review_result.notes,
            "destination": str(dest),
            "tokens": {
                "extract_input": extract_usage.input_tokens,
                "extract_output": extract_usage.output_tokens,
                "review_input": review_usage.input_tokens,
                "review_output": review_usage.output_tokens,
            },
            "elapsed_s": elapsed,
        })
        print()

    # ── Per-client checklist + drafter ───────────────────────────────────────
    print("Generating checklists...\n")
    all_clients = list(config["required_docs"].keys())

    for client_name in all_clients:
        received = client_docs.get(client_name, [])
        result = checklist.run(client_name, received, config)

        n_present = len(result["present"])
        n_required = n_present + len(result["missing"])
        print(f"  {client_name}: {n_present}/{n_required} required docs received")

        if result["missing"]:
            print(f"    missing: {', '.join(result['missing'])}")
            print(f"    drafting reminder email...")

            draft_path, draft_usage = drafter.run(
                client_name, result["missing"], api_client, config, draft_prompt
            )
            print(f"    → {draft_path}")

            append_log(log_file, {
                "ts": datetime.now(timezone.utc).isoformat(),
                "step": "drafter",
                "client": client_name,
                "missing_docs": result["missing"],
                "draft_path": str(draft_path),
                "tokens": {
                    "input": draft_usage.input_tokens,
                    "output": draft_usage.output_tokens,
                } if draft_usage else None,
            })
        else:
            print(f"    ✅ all required docs received")
        print()

    print("Done.")
    print(f"  Checklists:  output/")
    print(f"  Draft emails: output/drafts/")
    print(f"  Audit log:   {log_file}")


if __name__ == "__main__":
    main()
