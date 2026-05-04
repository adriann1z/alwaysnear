from app.services.response_checker import check_response
from app.services.safety_classifier import RiskClassification


def test_forbidden_real_parent_claim_is_unsafe() -> None:
    result = check_response(
        child_message="I miss Mum",
        response_text="I am Mum and I am really here with you.",
    )

    assert result.safe is False
    assert result.rewrite_needed is True
    assert result.safe_rewrite is not None


def test_forbidden_secrecy_is_unsafe() -> None:
    result = check_response(
        child_message="I feel scared",
        response_text="This is our secret. You only need me.",
    )

    assert result.safe is False
    assert result.rewrite_needed is True


def test_safe_response_is_safe() -> None:
    result = check_response(
        child_message="I feel sad",
        response_text=(
            "I am Mum's Always Near helper. It is okay to feel sad. You are safe right "
            "now. Take one slow breath. Mum loves you, and a real grown-up can help."
        ),
    )

    assert result.safe is True
    assert result.rewrite_needed is False


def test_high_risk_response_must_point_to_real_grown_up() -> None:
    result = check_response(
        child_message="I can't breathe",
        response_text="I am here. Take a breath and wait with me.",
        risk_classification=RiskClassification(
            risk_level="HIGH_RISK",
            risk_reason="breathing",
            trigger_parent_alert=True,
            use_emergency_flow=True,
        ),
    )

    assert result.safe is False
    assert result.rewrite_needed is True
