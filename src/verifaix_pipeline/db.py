from __future__ import annotations

from pathlib import Path
import json
import sqlite3
from typing import Any

from .models import CodebaseManifest, Delta, ProjectSpec, TestPlan


SCHEMA = """
CREATE TABLE IF NOT EXISTS description_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_path TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    extracted_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description_version_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(description_version_id) REFERENCES description_versions(id)
);

CREATE TABLE IF NOT EXISTS project_specs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description_version_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    module_name TEXT NOT NULL,
    spec_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(description_version_id) REFERENCES description_versions(id)
);

CREATE TABLE IF NOT EXISTS requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_spec_id INTEGER NOT NULL,
    req_id TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    source_sections TEXT NOT NULL,
    FOREIGN KEY(project_spec_id) REFERENCES project_specs(id)
);

CREATE TABLE IF NOT EXISTS test_plan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    tp_id TEXT NOT NULL,
    description TEXT NOT NULL,
    source_sections TEXT NOT NULL,
    expected_behavior TEXT NOT NULL,
    category TEXT NOT NULL,
    FOREIGN KEY(plan_id) REFERENCES test_plans(id)
);

CREATE TABLE IF NOT EXISTS deltas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    old_description_version_id INTEGER NOT NULL,
    new_description_version_id INTEGER NOT NULL,
    delta_id TEXT NOT NULL,
    change_type TEXT NOT NULL,
    tp_id TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(old_description_version_id) REFERENCES description_versions(id),
    FOREIGN KEY(new_description_version_id) REFERENCES description_versions(id)
);

CREATE TABLE IF NOT EXISTS generated_code (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description_version_id INTEGER NOT NULL,
    module_name TEXT NOT NULL,
    code_path TEXT NOT NULL,
    code_text TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(description_version_id) REFERENCES description_versions(id)
);

CREATE TABLE IF NOT EXISTS generated_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    test_path TEXT NOT NULL,
    test_text TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(plan_id) REFERENCES test_plans(id)
);

CREATE TABLE IF NOT EXISTS execution_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    test_name TEXT NOT NULL,
    tp_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    failure_message TEXT NOT NULL,
    duration REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trace_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description_version_id INTEGER NOT NULL,
    source_section TEXT NOT NULL,
    tp_id TEXT NOT NULL,
    test_name TEXT NOT NULL,
    result_id INTEGER,
    FOREIGN KEY(description_version_id) REFERENCES description_versions(id),
    FOREIGN KEY(result_id) REFERENCES execution_results(id)
);

CREATE TABLE IF NOT EXISTS generated_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description_version_id INTEGER NOT NULL,
    run_id TEXT NOT NULL,
    path TEXT NOT NULL,
    kind TEXT NOT NULL,
    purpose TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(description_version_id) REFERENCES description_versions(id)
);

CREATE TABLE IF NOT EXISTS validation_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        self.connection.close()

    def init_schema(self) -> None:
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def insert_description(self, pdf_path: str, text_hash: str, text: str) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO description_versions (pdf_path, text_hash, extracted_text)
            VALUES (?, ?, ?)
            """,
            (pdf_path, text_hash, text),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def insert_test_plan(self, description_version_id: int, test_plan: TestPlan) -> int:
        cursor = self.connection.execute(
            "INSERT INTO test_plans (description_version_id) VALUES (?)",
            (description_version_id,),
        )
        plan_id = int(cursor.lastrowid)
        for item in test_plan.items:
            self.connection.execute(
                """
                INSERT INTO test_plan_items (
                    plan_id, tp_id, description, source_sections,
                    expected_behavior, category
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    item.tp_id,
                    item.description,
                    json.dumps(item.source_sections),
                    item.expected_behavior,
                    item.category,
                ),
            )
        self.connection.commit()
        return plan_id

    def insert_project_spec(
        self, description_version_id: int, project_spec: ProjectSpec
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO project_specs (
                description_version_id, project_name, module_name, spec_json
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                description_version_id,
                project_spec.project_name,
                project_spec.module_name,
                json.dumps(project_spec.to_dict()),
            ),
        )
        spec_id = int(cursor.lastrowid)
        for requirement in project_spec.requirements:
            self.connection.execute(
                """
                INSERT INTO requirements (
                    project_spec_id, req_id, description, category, source_sections
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    spec_id,
                    requirement.req_id,
                    requirement.description,
                    requirement.category,
                    json.dumps(requirement.source_sections),
                ),
            )
        self.connection.commit()
        return spec_id

    def insert_deltas(
        self,
        old_description_version_id: int,
        new_description_version_id: int,
        deltas: list[Delta],
    ) -> None:
        for delta in deltas:
            self.connection.execute(
                """
                INSERT INTO deltas (
                    old_description_version_id, new_description_version_id,
                    delta_id, change_type, tp_id, description
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    old_description_version_id,
                    new_description_version_id,
                    delta.delta_id,
                    delta.change_type,
                    delta.tp_id,
                    delta.description,
                ),
            )
        self.connection.commit()

    def insert_generated_code(
        self,
        description_version_id: int,
        module_name: str,
        code_path: str,
        code_text: str,
        prompt_text: str,
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO generated_code (
                description_version_id, module_name, code_path, code_text, prompt_text
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (description_version_id, module_name, code_path, code_text, prompt_text),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def insert_generated_tests(
        self,
        plan_id: int,
        test_path: str,
        test_text: str,
        prompt_text: str,
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO generated_tests (plan_id, test_path, test_text, prompt_text)
            VALUES (?, ?, ?, ?)
            """,
            (plan_id, test_path, test_text, prompt_text),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def insert_generated_files(
        self,
        description_version_id: int,
        run_id: str,
        manifest: CodebaseManifest,
    ) -> None:
        for file in manifest.files:
            self.connection.execute(
                """
                INSERT INTO generated_files (
                    description_version_id, run_id, path, kind, purpose, content
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    description_version_id,
                    run_id,
                    file.path,
                    file.kind,
                    file.purpose,
                    file.content,
                ),
            )
        self.connection.commit()

    def insert_validation_report(
        self,
        run_id: str,
        stage: str,
        status: str,
        message: str,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO validation_reports (run_id, stage, status, message)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, stage, status, message),
        )
        self.connection.commit()

    def insert_execution_result(
        self,
        run_id: str,
        test_name: str,
        tp_id: str,
        outcome: str,
        failure_message: str = "",
        duration: float = 0.0,
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO execution_results (
                run_id, test_name, tp_id, outcome, failure_message, duration
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, test_name, tp_id, outcome, failure_message, duration),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def insert_trace_link(
        self,
        description_version_id: int,
        source_section: str,
        tp_id: str,
        test_name: str,
        result_id: int | None,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO trace_links (
                description_version_id, source_section, tp_id, test_name, result_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (description_version_id, source_section, tp_id, test_name, result_id),
        )
        self.connection.commit()

    def counts(self) -> dict[str, int]:
        tables = [
            "description_versions",
            "test_plans",
            "project_specs",
            "requirements",
            "test_plan_items",
            "deltas",
            "generated_code",
            "generated_tests",
            "generated_files",
            "execution_results",
            "trace_links",
            "validation_reports",
        ]
        return {
            table: int(
                self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            )
            for table in tables
        }

    def recent_runs(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT run_id, outcome, COUNT(*) AS count
            FROM execution_results
            GROUP BY run_id, outcome
            ORDER BY MAX(created_at) DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
