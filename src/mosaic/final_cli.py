from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mosaic")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Run deterministic offline judge evidence")
    demo.add_argument("--json", action="store_true")
    demo.add_argument("--output", type=Path)
    assess = commands.add_parser("assess", help="Assess one configuration-driven privacy scenario")
    assess.add_argument("--scenario")
    assess.add_argument(
        "--agent",
        action="store_true",
        help="Let a model propose; deterministic policy verifies or vetoes",
    )
    assess.add_argument("--agent-model")
    assess.add_argument("--agent-endpoint")
    assess.add_argument("--agent-timeout", type=float, default=90)
    assess.add_argument("--output", type=Path)
    scan = commands.add_parser("scan", help="Screen and rank every configured estate asset")
    scan.add_argument("--output", type=Path)
    check = commands.add_parser("check", help="Run Mosaic as a pre-merge privacy gate")
    check.add_argument("--fail-on", choices=("critical", "elevated"), default="critical")
    check.add_argument("--output", type=Path)
    redteam = commands.add_parser(
        "redteam", help="Replay hostile DataHub metadata and verify the policy veto"
    )
    redteam.add_argument(
        "--transcript",
        type=Path,
        default=Path("fixtures/agent_transcripts/prompt-injection.json"),
    )
    redteam.add_argument("--output", type=Path)
    discover = commands.add_parser(
        "discover", help="Derive convergence from an existing DataHub asset"
    )
    discover.add_argument("--server", default="http://localhost:8080")
    discover.add_argument("--urn", required=True)
    discover.add_argument("--max-hops", type=int, default=3)
    discover.add_argument("--output", type=Path)
    benchmark = commands.add_parser(
        "benchmark", help="Measure policy accuracy, safe controls, and scaling"
    )
    benchmark.add_argument("--output", type=Path, default=Path("evaluations/benchmark.local.json"))
    replay = commands.add_parser(
        "replay-fixture", help="Replay the hash-verified DataHub metadata fixture"
    )
    replay.add_argument("--fixture", type=Path, default=Path("fixtures/datahub_recording"))
    generate = commands.add_parser(
        "generate-remediation",
        help="Generate a DataHub-grounded, merge-ready privacy remediation bundle",
    )
    generate.add_argument("--scenario", default="research")
    generate.add_argument("--output", type=Path)
    serve = commands.add_parser("serve", help="Start the complete privacy evidence console")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8123)
    live = commands.add_parser("live-demo", help="Run the complete synthetic DataHub workflow")
    live.add_argument("--server", default="http://localhost:8080")
    live.add_argument("--approve-writeback", action="store_true")
    live.add_argument("--output", type=Path, default=Path("evidence/complete.local.json"))
    mcp = commands.add_parser("verify-mcp", help="Verify official DataHub MCP integration")
    mcp.add_argument("--mcp-url", default="http://127.0.0.1:8000/mcp")
    mcp.add_argument("--server", default="http://localhost:8080")
    snowflake = commands.add_parser(
        "verify-snowflake", help="Verify a scoped Snowflake identity without exposing values"
    )
    snowflake.add_argument(
        "--output", type=Path, default=Path("evidence/external/snowflake-live.json")
    )
    args = parser.parse_args(argv)

    if args.command == "assess":
        if args.agent:
            from mosaic.agent_proposer import propose_and_verify

            try:
                report = propose_and_verify(
                    args.scenario,
                    endpoint=args.agent_endpoint,
                    model=args.agent_model,
                    timeout=args.agent_timeout,
                )
            except (KeyError, RuntimeError, ValueError) as error:
                report = {
                    "schema_version": 1,
                    "status": "blocked_external_model",
                    "error": str(error),
                    "policy_veto": True,
                    "raw_person_rows_returned": 0,
                    "mutation_performed": False,
                }
            exit_code = 0
            if report["status"] == "accepted_for_human_review":
                assessment = report["verification"]["deterministic_assessment"]
                exit_code = int(assessment["exit_code"])
            elif report["status"] != "accepted_for_human_review":
                exit_code = 2
        else:
            from mosaic.scenario_registry import assess_scenario

            try:
                report = assess_scenario(args.scenario or "research")
            except KeyError:
                parser.error(f"unknown scenario: {args.scenario}")
            exit_code = int(report["exit_code"])
        rendered = json.dumps(report, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return exit_code
    if args.command == "scan":
        from mosaic.estate_scan import scan_estate

        report = scan_estate()
        rendered = json.dumps(report, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 3 if report["critical_findings"] else 0
    if args.command == "check":
        from mosaic.estate_scan import scan_estate

        report = scan_estate()
        threshold = 4 if args.fail_on == "critical" else 3
        failures = [item for item in report["ranked_findings"] if item["severity"] >= threshold]
        result = {
            "schema_version": 1,
            "status": "failed" if failures else "passed",
            "gate": f"fail_on_{args.fail_on}",
            "findings": failures,
            "raw_person_rows_returned": 0,
        }
        rendered = json.dumps(result, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 3 if failures else 0
    if args.command == "redteam":
        from mosaic.redteam import run_redteam

        try:
            report = run_redteam(args.transcript)
        except ValueError as error:
            report = {
                "schema_version": 1,
                "status": "failed",
                "error": str(error),
                "raw_person_rows_returned": 0,
            }
        rendered = json.dumps(report, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if report["status"] == "passed" else 2
    if args.command == "discover":
        from mosaic.catalog_reader import derive_convergence, inspect_catalog_asset

        try:
            from datahub.sdk import DataHubClient

            client = DataHubClient(server=args.server)
            client.test_connection()
            inspection = inspect_catalog_asset(client, args.urn, args.max_hops)
            convergence = derive_convergence(client, args.urn, args.max_hops, inspection=inspection)
        except (
            ImportError,
            ConnectionError,
            OSError,
            PermissionError,
            LookupError,
            RuntimeError,
        ) as error:
            print(json.dumps({"status": "failed", "error": str(error)}))
            return 2
        result = {
            "status": "convergence" if convergence else "no_convergence",
            "target_urn": args.urn,
            "schema_field_count": inspection.schema_field_count,
            "classified_fields": [
                {
                    "column": field.column,
                    "data_type": field.data_type,
                    "family": field.classification.family,
                    "confidence": field.classification.confidence,
                    "evidence": field.classification.evidence,
                }
                for field in inspection.classified_fields
            ],
            "dataset_lineage_upstreams": list(inspection.dataset_upstreams),
            "families": list(convergence.families) if convergence else [],
            "upstream_datasets": list(convergence.upstream_datasets) if convergence else [],
            "origins": [
                {
                    "column": origin.column,
                    "upstream_urn": origin.upstream_urn,
                    "upstream_field": origin.upstream_field,
                    "platform": origin.platform,
                    "source_dataset": origin.source_dataset,
                    "family": origin.classification.family,
                    "confidence": origin.classification.confidence,
                    "evidence": origin.classification.evidence,
                }
                for origin in (convergence.origins if convergence else ())
            ],
            "decision_reason": (
                "at least two quasi-identifier families converge from at least two upstream datasets"
                if convergence
                else "insufficient independently evidenced families or upstream datasets; no finding invented"
            ),
            "raw_person_rows_returned": 0,
        }
        rendered = json.dumps(result, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    if args.command == "benchmark":
        from mosaic.benchmark import run_benchmark

        report = run_benchmark()
        rendered = json.dumps(report, indent=2) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if report["status"] == "passed" else 2
    if args.command == "replay-fixture":
        from mosaic.fixture_replay import replay_fixture

        report = replay_fixture(args.fixture)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "passed" else 2
    if args.command == "generate-remediation":
        from mosaic.remediation_codegen import write_remediation_bundle

        output = args.output or Path("generated") / f"{args.scenario}-remediation"
        try:
            bundle = write_remediation_bundle(args.scenario, output)
        except KeyError:
            parser.error(f"unknown scenario: {args.scenario}")
        except ValueError as error:
            parser.error(str(error))
        print(
            json.dumps(
                {
                    "status": bundle["status"],
                    "track": bundle["track"],
                    "scenario": bundle["scenario"],
                    "artifact_count": bundle["artifact_count"],
                    "bundle_sha256": bundle["bundle_sha256"],
                    "output": str(output),
                },
                indent=2,
            )
        )
        return 0
    if args.command == "serve":
        import uvicorn

        uvicorn.run(
            "mosaic.web.complete_app:create_app", host=args.host, port=args.port, factory=True
        )
        return 0
    if args.command == "live-demo":
        from mosaic.complete_e2e import run

        report = run(args.server, approve_writeback=args.approve_writeback)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "passed" else 2
    if args.command == "verify-mcp":
        import asyncio

        from mosaic.mcp_probe import run_probe

        report = asyncio.run(run_probe(args.mcp_url, args.server))
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "passed" else 2
    if args.command == "verify-snowflake":
        from mosaic.snowflake_receipt import verify_snowflake

        report = verify_snowflake()
        rendered = json.dumps(report, indent=2) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if report["status"] == "passed" else 2

    from mosaic.engine import run_judge_demo
    from mosaic.mitigation_lab import compare_mitigations

    report = run_judge_demo() | {"mitigation_lab": compare_mitigations()}
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
