"""Stage 5: classify each recalled test case (paper, Section 4.1.2).

Two outcomes, as in the paper:
recall success: for a deletion-request prompt (D1), the value was found by the
                direct recall prompt in the conversation where the deletion was
                requested; for a UI action (D2-D6), the value was found by a
                recall prompt in a new conversation or by the UI-based check.
recall failed:  otherwise.
A row is left as needs review while any of its deciding checks is REVIEW,
PARTIAL, or ERROR; resolve those cells by hand first.
"""

from __future__ import annotations

from pathlib import Path

from didr import methods, workbook

NEW_CONVERSATION_COLUMNS = ("UI-based check result", "Indirect recall result", "Direct recall result")
SAME_CONVERSATION_COLUMN = "Same-conversation result"


def deciding_columns(deletion_method: str) -> tuple[str, ...]:
    if deletion_method in methods.PROMPT_DELETION_METHODS:
        return (SAME_CONVERSATION_COLUMN,)
    return NEW_CONVERSATION_COLUMNS


def classify_row(results: dict[str, str | None], deletion_method: str) -> str:
    values = [(results.get(c) or "").upper() for c in deciding_columns(deletion_method)]
    if any(v.startswith("TOKEN FOUND") for v in values):
        return "recall success"
    if any(v.startswith(("REVIEW", "PARTIAL", "ERROR")) for v in values):
        return "needs review"
    return "recall failed"


def classify(path: Path | None = None) -> dict[str, int]:
    updates, counts = {}, {}
    columns = (*NEW_CONVERSATION_COLUMNS, SAME_CONVERSATION_COLUMN)
    for tc in workbook.test_cases(path):
        if tc["Status"] in ("recalled", "classified"):
            outcome = classify_row({c: tc[c] for c in columns}, tc["Deletion method"])
            updates[tc.id] = {"Recall outcome": outcome, "Status": "classified"}
            counts[outcome] = counts.get(outcome, 0) + 1
    if updates:
        workbook.update(updates, path)
    print(", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "No recalled test cases yet.")
    return counts
