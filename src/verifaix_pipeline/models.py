from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Description:
    pdf_path: str
    text: str
    text_hash: str


@dataclass(frozen=True)
class PublicAPI:
    name: str
    kind: str
    signature: str
    description: str
    source_sections: list[str]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PublicAPI":
        sections = raw.get("source_sections", [])
        if isinstance(sections, str):
            sections = [sections]
        api = cls(
            name=str(raw["name"]),
            kind=str(raw.get("kind", "function")),
            signature=str(raw.get("signature", raw["name"])),
            description=str(raw.get("description", "")),
            source_sections=[str(section) for section in sections],
        )
        if not api.name.strip():
            raise ValueError("Public API name cannot be empty")
        if api.kind not in {"function", "class"}:
            raise ValueError(f"Unsupported public API kind: {api.kind}")
        return api

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "signature": self.signature,
            "description": self.description,
            "source_sections": self.source_sections,
        }


@dataclass(frozen=True)
class Requirement:
    req_id: str
    description: str
    category: str
    source_sections: list[str]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Requirement":
        sections = raw.get("source_sections", [])
        if isinstance(sections, str):
            sections = [sections]
        requirement = cls(
            req_id=str(raw["req_id"]),
            description=str(raw["description"]),
            category=str(raw.get("category", "behavior")),
            source_sections=[str(section) for section in sections],
        )
        if not requirement.req_id.startswith("REQ_"):
            raise ValueError(f"Invalid requirement ID: {requirement.req_id}")
        if not requirement.description.strip():
            raise ValueError(f"{requirement.req_id} has an empty description")
        return requirement

    def to_dict(self) -> dict[str, Any]:
        return {
            "req_id": self.req_id,
            "description": self.description,
            "category": self.category,
            "source_sections": self.source_sections,
        }


@dataclass(frozen=True)
class ProjectSpec:
    project_name: str
    module_name: str
    public_api: list[PublicAPI]
    requirements: list[Requirement]
    constraints: dict[str, Any]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ProjectSpec":
        public_api = [PublicAPI.from_dict(item) for item in raw.get("public_api", [])]
        requirements = [
            Requirement.from_dict(item) for item in raw.get("requirements", [])
        ]
        spec = cls(
            project_name=str(raw.get("project_name", raw.get("module_name", "generated_project"))),
            module_name=str(raw["module_name"]),
            public_api=public_api,
            requirements=requirements,
            constraints=dict(raw.get("constraints", {})),
        )
        if not spec.project_name.strip():
            raise ValueError("Project name cannot be empty")
        if not spec.module_name.strip():
            raise ValueError("Module name cannot be empty")
        if not spec.public_api:
            raise ValueError("Project spec must contain at least one public API")
        if not spec.requirements:
            raise ValueError("Project spec must contain at least one requirement")
        return spec

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "module_name": self.module_name,
            "public_api": [item.to_dict() for item in self.public_api],
            "requirements": [item.to_dict() for item in self.requirements],
            "constraints": self.constraints,
        }


@dataclass(frozen=True)
class TestPlanItem:
    tp_id: str
    description: str
    source_sections: list[str]
    expected_behavior: str
    category: str
    requirement_ids: list[str] | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TestPlanItem":
        source_sections = raw.get("source_sections", [])
        if isinstance(source_sections, str):
            source_sections = [source_sections]
        requirement_ids = raw.get("requirement_ids")
        if isinstance(requirement_ids, str):
            requirement_ids = [requirement_ids]
        item = cls(
            tp_id=str(raw["tp_id"]),
            description=str(raw["description"]),
            source_sections=[str(section) for section in source_sections],
            expected_behavior=str(raw.get("expected_behavior", raw["description"])),
            category=str(raw.get("category", "behavior")),
            requirement_ids=(
                [str(req_id) for req_id in requirement_ids]
                if requirement_ids is not None
                else None
            ),
        )
        item.validate()
        return item

    def validate(self) -> None:
        if not self.tp_id.startswith("TP_"):
            raise ValueError(f"Invalid test-plan ID: {self.tp_id}")
        if not self.description.strip():
            raise ValueError(f"{self.tp_id} has an empty description")
        if not self.expected_behavior.strip():
            raise ValueError(f"{self.tp_id} has an empty expected behavior")

    def to_dict(self) -> dict[str, Any]:
        return {
            "tp_id": self.tp_id,
            "description": self.description,
            "source_sections": self.source_sections,
            "expected_behavior": self.expected_behavior,
            "category": self.category,
            "requirement_ids": self.requirement_ids or [],
        }


@dataclass(frozen=True)
class TestPlan:
    items: list[TestPlanItem]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TestPlan":
        items = [TestPlanItem.from_dict(item) for item in raw.get("items", [])]
        if not items:
            raise ValueError("Test plan must contain at least one item")
        seen = set()
        for item in items:
            if item.tp_id in seen:
                raise ValueError(f"Duplicate test-plan ID: {item.tp_id}")
            seen.add(item.tp_id)
        return cls(items=items)

    def to_dict(self) -> dict[str, Any]:
        return {"items": [item.to_dict() for item in self.items]}


@dataclass(frozen=True)
class Delta:
    delta_id: str
    change_type: str
    tp_id: str
    description: str


@dataclass(frozen=True)
class GeneratedFile:
    path: str
    kind: str
    purpose: str
    content: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "GeneratedFile":
        file = cls(
            path=str(raw["path"]),
            kind=str(raw.get("kind", "source")),
            purpose=str(raw.get("purpose", "")),
            content=str(raw.get("content", "")),
        )
        if file.kind not in {"source", "test", "support"}:
            raise ValueError(f"Unsupported generated file kind: {file.kind}")
        if not file.path.strip():
            raise ValueError("Generated file path cannot be empty")
        return file

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "purpose": self.purpose,
            "content": self.content,
        }


@dataclass(frozen=True)
class CodebaseManifest:
    entry_module: str
    files: list[GeneratedFile]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "CodebaseManifest":
        files = [GeneratedFile.from_dict(item) for item in raw.get("files", [])]
        manifest = cls(entry_module=str(raw["entry_module"]), files=files)
        if not manifest.entry_module.strip():
            raise ValueError("Codebase manifest entry_module cannot be empty")
        if not manifest.files:
            raise ValueError("Codebase manifest must contain files")
        return manifest

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_module": self.entry_module,
            "files": [file.to_dict() for file in self.files],
        }
