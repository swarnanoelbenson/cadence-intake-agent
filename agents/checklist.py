"""
Step 4: Compare what we received against what we expected for each client.
Writes a Markdown checklist to output/<ClientName>_checklist.md.
Returns a dict with 'missing', 'present', and 'path' keys.
"""

from pathlib import Path


def run(client_name: str, received_docs: list[str], config: dict) -> dict:
    required = set(config["required_docs"].get(client_name, []))
    received = set(received_docs)

    present = required & received
    missing = required - received
    extra = received - required   # docs received but not in the required list

    client_slug = client_name.replace(" ", "_")
    output_path = Path("output") / f"{client_slug}_checklist.md"
    output_path.parent.mkdir(exist_ok=True)

    lines = [
        f"# Document Checklist — {client_name}",
        "",
        "**Financial Year:** 2024–25",
        "",
        "## Required Documents",
        "",
    ]

    for doc in sorted(required):
        status = "✅" if doc in present else "❌"
        lines.append(f"- {status} `{doc}`")

    if extra:
        lines += ["", "## Additional Documents Received", ""]
        for doc in sorted(extra):
            lines.append(f"- ⬜ `{doc}` *(not in required list)*")

    if missing:
        status_line = f"**Status:** {len(missing)} document(s) missing — reminder email drafted."
    else:
        status_line = "**Status:** All required documents received. ✅"

    lines += ["", status_line]

    output_path.write_text("\n".join(lines) + "\n")

    return {
        "missing": sorted(missing),
        "present": sorted(present),
        "path": str(output_path),
    }
