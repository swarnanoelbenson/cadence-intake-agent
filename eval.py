"""
Evaluate the classifier against tests/ground_truth.csv.

Runs the classifier (Step 1 only) on each PDF in inbox/ and compares the
result to the known-good answers. Prints three metrics:

  - Classification accuracy   (doc_type correct ?)
  - Client name accuracy      (client_name correct ?)
  - Key field accuracy        (extracted amounts within $1 of ground truth ?)
  - Human-review rate         (confidence < threshold ?)

Usage:  python eval.py
"""

import csv
from pathlib import Path

import anthropic
import yaml

from agents import classifier_extractor


def normalise(name: str) -> str:
    return name.lower().strip()


def amounts_match(actual: str, expected: str, tolerance: float = 1.0) -> bool:
    try:
        return abs(float(actual) - float(expected)) <= tolerance
    except (ValueError, TypeError):
        return normalise(str(actual)) == normalise(str(expected))


def main() -> None:
    config = yaml.safe_load(Path("config.yaml").read_text())
    api_client = anthropic.Anthropic()
    prompt = Path("prompts/classifier_extractor.md").read_text()

    gt_path = Path("tests/ground_truth.csv")
    if not gt_path.exists():
        print("Ground truth not found. Run:  python scripts/make_samples.py")
        return

    rows = list(csv.DictReader(gt_path.open()))
    print(f"Evaluating {len(rows)} document(s)...\n")

    total = 0
    correct_type = 0
    correct_client = 0
    human_review_count = 0
    field_matches = 0
    field_total = 0

    for row in rows:
        pdf_path = Path("inbox") / row["filename"]
        if not pdf_path.exists():
            print(f"  SKIP {row['filename']} (file not found in inbox/)")
            continue

        result, _ = classifier_extractor.run(pdf_path, api_client, config, prompt)
        total += 1

        type_ok = result.doc_type == row["doc_type"]
        client_ok = normalise(result.client_name) == normalise(row["client"])
        if type_ok:
            correct_type += 1
        if client_ok:
            correct_client += 1
        if result.confidence < config["confidence_threshold"]:
            human_review_count += 1

        # Parse expected amounts: "gross_income=85000.00,tax_withheld=19200.00"
        expected_amounts: dict[str, str] = {}
        for part in row.get("key_amounts", "").split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                expected_amounts[k.strip()] = v.strip()

        for key, expected_val in expected_amounts.items():
            if not expected_val:
                continue
            field_total += 1
            actual_val = str(result.key_fields.get(key, ""))
            if amounts_match(actual_val, expected_val):
                field_matches += 1

        type_mark = "✓" if type_ok else "✗"
        client_mark = "✓" if client_ok else "✗"
        print(
            f"  {type_mark} type | {client_mark} client | "
            f"conf={result.confidence:.2f} | "
            f"{result.doc_type} ← {row['filename']}"
        )
        if not type_ok:
            print(f"      expected type={row['doc_type']!r}  got={result.doc_type!r}")
        if not client_ok:
            print(f"      expected client={row['client']!r}  got={result.client_name!r}")

    if total == 0:
        print("No documents evaluated.")
        return

    print(f"\n{'=' * 55}")
    print(f"Documents evaluated:    {total}")
    print(f"Classification accuracy: {correct_type}/{total}  ({100 * correct_type / total:.0f}%)")
    print(f"Client name accuracy:    {correct_client}/{total}  ({100 * correct_client / total:.0f}%)")
    if field_total:
        print(f"Key field accuracy:      {field_matches}/{field_total}  ({100 * field_matches / field_total:.0f}%)")
    print(f"Sent to human review:    {human_review_count}/{total}  ({100 * human_review_count / total:.0f}%)")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
