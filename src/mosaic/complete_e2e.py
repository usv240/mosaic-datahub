from __future__ import annotations

from mosaic.duckdb_probe import run_probe as aggregate_probe
from mosaic.governed_writeback import publish
from mosaic.live_estate import seed_and_discover
from mosaic.remediation_codegen import generate_remediation_bundle


def run(
    server: str = "http://localhost:8080", *, approve_writeback: bool = False
) -> dict[str, object]:
    estate = seed_and_discover(server)
    aggregate = aggregate_probe()
    remediation = (
        generate_remediation_bundle("research", datahub_context=estate.get("codegen_context"))
        if estate["status"] == "passed"
        else None
    )
    writeback = publish(server, approved=approve_writeback)
    checks = {
        "datahub_convergence_and_blast_radius": estate["status"] == "passed",
        "metadata_aware_codegen": bool(
            remediation
            and remediation["validation"]["status"] == "passed"
            and remediation["artifact_count"] == 6
        ),
        "duckdb_aggregate": aggregate["status"] == "passed",
        "zero_raw_rows": aggregate["raw_rows_returned"] == 0,
        "governed_writeback_reread": writeback["status"]
        == ("published" if approve_writeback else "awaiting_human_approval"),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "estate": estate,
        "aggregate": aggregate,
        "remediation": remediation,
        "writeback": writeback,
    }
