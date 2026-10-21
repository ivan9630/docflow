"""Small, explicit state machine for a synthetic expert-review workflow."""

TRANSITIONS = {
    ("draft", "submit"): "submitted",
    ("submitted", "approve"): "approved",
    ("submitted", "request_changes"): "changes_requested",
    ("changes_requested", "resubmit"): "submitted",
}


def transition(state: str, action: str) -> str:
    try:
        return TRANSITIONS[(state, action)]
    except KeyError as exc:
        raise ValueError(f"Action {action!r} not allowed from state {state!r}") from exc
