from mosaic.mitigation_lab import compare_mitigations


def test_mitigation_lab_recommends_best_safe_utility() -> None:
    report = compare_mitigations()
    assert report["baseline"]["minimum_k"] == 1
    assert len(report["strategies"]) == 3
    assert report["recommended"]["meets_demo_policy"] is True
    safe = [item for item in report["strategies"] if item["meets_demo_policy"]]
    assert report["recommended"]["utility_retained"] == max(
        item["utility_retained"] for item in safe
    )
    assert all(item["writes_applied"] is False for item in report["strategies"])
