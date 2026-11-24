"""
Step 5: Draft a polite reminder email for clients with missing documents.
Writes the draft to output/drafts/<client_slug>_reminder.txt.
NOTE: This only writes a file — it never sends anything.
"""

from pathlib import Path

import anthropic


def run(
    client_name: str,
    missing_docs: list[str],
    client: anthropic.Anthropic,
    config: dict,
    prompt_template: str,
) -> tuple[Path | None, anthropic.types.Usage | None]:
    if not missing_docs:
        return None, None

    # Format missing doc names for the prompt: "work_expense_receipt" → "Work Expense Receipt"
    docs_list = "\n".join(
        f"- {doc.replace('_', ' ').title()}" for doc in missing_docs
    )

    prompt = (
        prompt_template
        .replace("{CLIENT_NAME}", client_name)
        .replace("{MISSING_DOCS}", docs_list)
    )

    response = client.messages.create(
        model=config["model"],
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    email_text = next(b.text for b in response.content if b.type == "text")

    output_dir = Path("output/drafts")
    output_dir.mkdir(parents=True, exist_ok=True)

    client_slug = client_name.lower().replace(" ", "_")
    draft_path = output_dir / f"{client_slug}_reminder.txt"
    draft_path.write_text(email_text)

    return draft_path, response.usage
