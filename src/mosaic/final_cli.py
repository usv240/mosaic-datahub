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
    assess.add_argument("--scenario", default="research")
    assess.add_argument("--output", type=Path)
    scan = commands.add_parser("scan", help="Screen and rank every configured estate asset")
    scan.add_argument("--output", type=Path)
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
    args = parser.parse_args(argv)

    if args.command == "assess":
        from mosaic.scenario_registry import assess_scenario

        try:
            report = assess_scenario(args.scenario)
        except KeyError:
            parser.error(f"unknown scenario: {args.scenario}")
        rendered = json.dumps(report, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return int(report["exit_code"])
    if args.command == "scan":
        from mosaic.estate_scan import scan_estate

        report = scan_estate()
        rendered = json.dumps(report, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 3 if report["critical_findings"] else 0
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
