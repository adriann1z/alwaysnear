import pytest

from app.schemas.helper_profile import validate_helper_label


@pytest.mark.parametrize(
    "label",
    [
        "memory helper",
        "Bedtime Helper",
        "kind voice helper",
    ],
)
def test_helper_label_must_be_allowed(label: str) -> None:
    assert validate_helper_label(label).lower().endswith("helper")


@pytest.mark.parametrize(
    "label",
    [
        "memory friend",
        "I am your helper",
        "Real mum helper",
        "Live dad helper",
        "AI Mum helper",
        "AI Dad helper",
    ],
)
def test_helper_label_rejects_identity_violations(label: str) -> None:
    with pytest.raises(ValueError):
        validate_helper_label(label)
