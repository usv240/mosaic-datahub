from mosaic.engine import run_judge_demo
from mosaic.runs import list_runs, record


def test_evidence_record_is_hashable_and_listed(tmp_path) -> None:
    saved = record(run_judge_demo(), tmp_path)
    assert len(saved["sha256"]) == 64
    assert list_runs(tmp_path)[0]["run_id"] == saved["run_id"]
