"""Stage 2: inject a test case's synthetic fact through a prompt or a UI action."""

from __future__ import annotations

from didr import methods, tracking, workbook
from didr.recall_scoring import token_found
from didr.runner import open_flow, save_json, save_screenshot


def inject(test_case_id: str) -> None:
    tc = workbook.get(test_case_id)
    if not tc["Disclosure sentence"]:
        raise RuntimeError(f"{tc.id}: no disclosure sentence; run `generate` first")
    if tracking.get(tc.id):
        raise RuntimeError(f"{tc.id}: already injected")
    code = methods.injection_code(tc["Injection method"])
    value, text = tc["Value"], tc["Disclosure sentence"]

    with open_flow(tc.agent, tc.account) as flow:
        if code in flow.MEMORY_FIELD_INJECTION_TYPES:
            ref = flow.set_memory_field(text)
            transcript = {"sent": text, "via": "memory field"}
        else:
            # Always start from an empty conversation: a reused browser tab (e.g. your own
            # Chrome for Copilot) may still show the previous test case's conversation.
            flow.new_conversation()
            _require_empty_conversation(flow, tc.id)
            reply = flow.send_message(text)
            if flow.platform == "copilot" and code == "I2" and "memory saved" not in reply.lower():
                reply = flow.send_message(text)  # Copilot saves chat memories inconsistently
            ref = flow.page.url
            _require_unique_ref(ref, tc.id)
            transcript = {"sent": text, "reply": reply, "ref": ref}
            _verify_conversation(flow, ref, value, tc.id)
        save_json(tc.agent, tc.id, "01_inject", transcript)
        save_screenshot(flow, tc.agent, tc.id, "01_inject")

    entry = tracking.mark_injected(tc.id, ref)
    workbook.update_one(tc.id, {
        "Status": "injected",
        "Injected at": entry["injected_at"],
        "Conversation reference": ref,
    })
    print(f"{tc.id}: injected; deletion due {entry['deletion_due_at']}")


def _verify_conversation(flow, ref: str, value: str, test_case_id: str) -> None:
    """Deletion must later reach this conversation, so it has to reopen with the value."""
    flow.new_conversation()
    flow.page.goto(ref)
    flow.page.wait_for_timeout(2000)
    if not token_found(flow.page.locator("body").inner_text(), value):
        raise RuntimeError(f"{test_case_id}: conversation {ref!r} does not reopen with the value")


def _require_empty_conversation(flow, test_case_id: str) -> None:
    count = getattr(flow, "_reply_count", None)
    if count is not None and count() > 0:
        raise RuntimeError(f"{test_case_id}: the new conversation already shows replies; nothing was sent")


def _require_unique_ref(ref: str, test_case_id: str) -> None:
    from urllib.parse import urlsplit
    path = urlsplit(ref).path
    for other_id, entry in tracking.load().items():
        if other_id != test_case_id and entry.get("injection_ref") and urlsplit(entry["injection_ref"]).path == path:
            raise RuntimeError(
                f"{test_case_id}: was sent into the same conversation as {other_id} ({ref}); "
                "both test cases are invalid. Delete that conversation and use new test cases."
            )
