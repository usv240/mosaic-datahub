from mosaic.controls import run_safe_controls
from mosaic.scenario import build_synthetic_estate


def test_generalized_and_non_compositional_controls_clear() -> None:
    report = run_safe_controls(build_synthetic_estate())
    assert report["status"] == "passed"
    controls = {item["name"]: item for item in report["controls"]}
    assert controls["generalized_export"]["actual"] == "validated_low"
    assert controls["operational_identifier"]["actual"] == "not_critical"
