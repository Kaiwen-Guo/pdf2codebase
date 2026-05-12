from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .db import Database
from .pipeline import initialize_database, run_delta, run_pipeline, validate_artifact_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="verifaix")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_db = subparsers.add_parser("init-db", help="Initialize the SQLite schema")
    init_db.add_argument("--config", default="config.local.toml")

    run = subparsers.add_parser("run", help="Run PDF-to-tests pipeline")
    run.add_argument("--pdf", required=True)
    run.add_argument("--config", default="config.local.toml")

    delta = subparsers.add_parser("delta", help="Compare two description versions")
    delta.add_argument("--old-pdf", required=True)
    delta.add_argument("--new-pdf", required=True)
    delta.add_argument("--config", default="config.local.toml")

    show_runs = subparsers.add_parser("show-runs", help="Show recorded run outcomes")
    show_runs.add_argument("--db", default="verifaix.local.db")

    validate_run = subparsers.add_parser(
        "validate-run", help="Validate a generated artifact directory"
    )
    validate_run.add_argument("--artifact-dir", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-db":
        config = load_config(args.config)
        counts = initialize_database(config)
        print(f"Initialized database: {config.storage.database_path}")
        print(counts)
        return 0

    if args.command == "run":
        config = load_config(args.config)
        summary = run_pipeline(args.pdf, config)
        print(f"Run ID: {summary.run_id}")
        print(f"Description version: {summary.description_version_id}")
        print(f"Test plan: {summary.plan_id}")
        print(f"Module: {summary.module_name}")
        print(f"Artifacts: {summary.artifact_dir}")
        print(f"Pytest return code: {summary.pytest_returncode}")
        print(f"Passed: {summary.passed} Failed: {summary.failed}")
        return 0 if summary.pytest_returncode == 0 else 1

    if args.command == "delta":
        config = load_config(args.config)
        deltas = run_delta(args.old_pdf, args.new_pdf, config)
        for delta in deltas:
            print(
                f"{delta.delta_id}\t{delta.change_type}\t"
                f"{delta.tp_id}\t{delta.description}"
            )
        print(f"Delta count: {len(deltas)}")
        return 0

    if args.command == "show-runs":
        database = Database(Path(args.db))
        try:
            database.init_schema()
            for row in database.recent_runs():
                print(f"{row['run_id']}\t{row['outcome']}\t{row['count']}")
        finally:
            database.close()
        return 0

    if args.command == "validate-run":
        result = validate_artifact_dir(args.artifact_dir)
        for stage, status in result.items():
            print(f"{stage}\t{status}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
