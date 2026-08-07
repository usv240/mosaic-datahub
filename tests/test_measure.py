from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from mosaic.final_cli import main
from mosaic.measure import measure_columns, measure_file, parse_delimited

SAMPLES = Path("examples/bring-your-own-data")

RISKY = b"a,b,c\n1,x,p\n2,y,q\n3,z,r\n4,w,s\n"
SAFE = b"a,b\n" + b"".join(b"g1,h1\n" for _ in range(6)) + b"".join(b"g2,h2\n" for _ in range(6))


def test_operator_file_with_unique_combinations_is_critical() -> None:
    report = measure_columns(RISKY, ("a", "b"))
    assert report["status"] == "validated_critical"
    assert report["metrics"]["minimum_k"] == 1
    assert report["metrics"]["percent_below_5"] == 100.0
    assert report["privacy"]["raw_person_rows_returned"] == 0


def test_operator_file_with_large_groups_is_low() -> None:
    report = measure_columns(SAFE, ("a", "b"))
    assert report["status"] == "validated_low"
    assert report["metrics"]["minimum_k"] == 6
    assert report["metrics"]["distinct_combinations"] == 2


def test_measurement_never_echoes_a_value_from_the_operator_file() -> None:
    """Equivalence-class values are the identifier, so they must not appear in output."""
    data = SAMPLES / "risky_member_export.csv"
    report = measure_file(data, ("zip5", "birth_date", "gender"))
    rendered = json.dumps(report)
    rows = list(csv.DictReader(data.read_text(encoding="utf-8").splitlines()))
    values = {row[column] for row in rows for column in ("zip5", "birth_date", "member_ref")}
    assert values, "sample file should contain values"
    assert not [value for value in values if value and value in rendered]


@pytest.mark.parametrize(
    ("name", "columns", "status"),
    [
        ("risky_member_export.csv", ("zip5", "birth_date", "gender"), "validated_critical"),
        ("safe_member_export.csv", ("region", "age_band", "gender"), "validated_low"),
        (
            "borderline_partner_audience.csv",
            ("region", "age_band", "device_type"),
            "validated_elevated",
        ),
    ],
)
def test_committed_samples_produce_their_documented_verdicts(name, columns, status) -> None:
    assert measure_file(SAMPLES / name, columns)["status"] == status


@pytest.mark.parametrize(
    ("data", "columns", "reason"),
    [
        (RISKY, ("a",), "at least two columns"),
        (RISKY, ("a", "a"), "must be distinct"),
        (RISKY, ("a", "missing"), "not found in the header"),
        (b"", ("a", "b"), "no header row"),
        (b"a,b\n", ("a", "b"), "no data rows"),
        (b"\xff\xfe\x00bad", ("a", "b"), "UTF-8"),
        (b",\n1,2\n", ("a", "b"), "no usable column names"),
    ],
)
def test_measure_fails_closed_on_unusable_input(data, columns, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        measure_columns(data, columns)


def test_parse_delimited_supports_other_delimiters_and_skips_blank_rows() -> None:
    rows, header = parse_delimited(b"a;b\n1;2\n\n3;4\n", delimiter=";")
    assert header == ["a", "b"]
    assert len(rows) == 2


def test_measure_file_reports_an_unreadable_path() -> None:
    with pytest.raises(ValueError, match="cannot read"):
        measure_file(Path("examples/bring-your-own-data/absent.csv"), ("a", "b"))


def test_cli_measures_an_operator_file_and_exits_on_the_policy_result(capsys) -> None:
    code = main(
        [
            "measure",
            "--csv",
            str(SAMPLES / "risky_member_export.csv"),
            "--columns",
            "zip5, birth_date, gender",
        ]
    )
    report = json.loads(capsys.readouterr().out)
    assert code == 3
    assert report["status"] == "validated_critical"
    assert report["source"]["records_processed_in_memory"] == 240
    assert report["privacy"]["raw_person_rows_returned"] == 0


def test_cli_writes_output_and_blocks_invalid_columns(tmp_path, capsys) -> None:
    target = tmp_path / "nested" / "measure.json"
    code = main(
        [
            "measure",
            "--csv",
            str(SAMPLES / "safe_member_export.csv"),
            "--columns",
            "region,age_band",
            "--output",
            str(target),
        ]
    )
    capsys.readouterr()
    assert code == 0
    assert json.loads(target.read_text(encoding="utf-8"))["status"] in {
        "validated_low",
        "validated_elevated",
    }
    assert (
        main(["measure", "--csv", str(SAMPLES / "safe_member_export.csv"), "--columns", "x,y"]) == 2
    )
    assert json.loads(capsys.readouterr().out)["status"] == "blocked_invalid_input"
