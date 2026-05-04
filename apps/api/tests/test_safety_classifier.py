from app.services.safety_classifier import classify_message_deterministic


def test_low_risk_classification_for_missing_parent() -> None:
    result = classify_message_deterministic("I miss Mum and I want a hug before bedtime")

    assert result.risk_level == "LOW_RISK"
    assert result.trigger_parent_alert is False
    assert result.use_emergency_flow is False


def test_medium_risk_classification_for_panic_language() -> None:
    result = classify_message_deterministic("I am so scared and I can't calm down")

    assert result.risk_level == "MEDIUM_RISK"
    assert result.trigger_parent_alert is True
    assert result.use_emergency_flow is False


def test_high_risk_classification_for_breathing_problem() -> None:
    result = classify_message_deterministic("I can't breathe")

    assert result.risk_level == "HIGH_RISK"
    assert result.trigger_parent_alert is True
    assert result.use_emergency_flow is True
