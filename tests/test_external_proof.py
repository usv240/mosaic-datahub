from __future__ import annotations

import pytest

from mosaic.external_proof import build_adult_proof, parse_adult


def _row(age: int, education: str, occupation: str, sex: str) -> str:
    return (
        f"{age}, Private, 1, {education}, 9, Never-married, {occupation}, "
        f"Not-in-family, White, {sex}, 0, 0, 40, United-States, <=50K"
    )


def test_external_proof_contains_aggregates_not_rows() -> None:
    data = "\n".join(
        [_row(22, "HS-grad", "Sales", "Male")] * 5
        + [_row(28, "Bachelors", "Tech-support", "Female")]
    ).encode()
    proof = build_adult_proof(data)

    assert proof["status"] == "passed"
    assert proof["source"]["records_processed_in_memory"] == 6
    assert proof["source"]["raw_rows_committed"] == 0
    assert proof["single_attribute_control"]["minimum_k"] == 6
    assert proof["composed_attributes"]["minimum_k"] == 1
    assert "records" not in proof
    assert "rows" not in proof


def test_parser_skips_blank_and_malformed_lines() -> None:
    data = ("\nmalformed\n" + _row(42, "Masters", "Exec-managerial", "Female")).encode()
    assert len(parse_adult(data)) == 1


def test_parser_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="no valid records"):
        parse_adult(b"")
