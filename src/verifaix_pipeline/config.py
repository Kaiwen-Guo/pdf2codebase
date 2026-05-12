from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class LLMConfig:
    llm_provider: str
    model_name: str
    api_key_env: str
    temperature: float
    use_llm_for_testplan: bool
    use_llm_for_code: bool
    use_llm_for_tests: bool


@dataclass(frozen=True)
class StorageConfig:
    database_path: Path
    artifacts_dir: Path


@dataclass(frozen=True)
class RuntimeConfig:
    module_name: str
    fallback_to_deterministic: bool


@dataclass(frozen=True)
class AppConfig:
    llm: LLMConfig
    storage: StorageConfig
    runtime: RuntimeConfig


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    llm_raw = raw.get("llm", {})
    storage_raw = raw.get("storage", {})
    runtime_raw = raw.get("runtime", {})

    base_dir = config_path.parent
    database_path = Path(storage_raw.get("database_path", "verifaix.db"))
    artifacts_dir = Path(storage_raw.get("artifacts_dir", "artifacts"))
    if not database_path.is_absolute():
        database_path = base_dir / database_path
    if not artifacts_dir.is_absolute():
        artifacts_dir = base_dir / artifacts_dir

    provider = str(llm_raw.get("llm_provider", "none")).lower()
    if provider not in {"none", "openai"}:
        raise ValueError(f"Unsupported llm_provider: {provider}")

    return AppConfig(
        llm=LLMConfig(
            llm_provider=provider,
            model_name=str(llm_raw.get("model_name", "")),
            api_key_env=str(llm_raw.get("api_key_env", "")),
            temperature=float(llm_raw.get("temperature", 0.0)),
            use_llm_for_testplan=bool(llm_raw.get("use_llm_for_testplan", False)),
            use_llm_for_code=bool(llm_raw.get("use_llm_for_code", False)),
            use_llm_for_tests=bool(llm_raw.get("use_llm_for_tests", False)),
        ),
        storage=StorageConfig(
            database_path=database_path,
            artifacts_dir=artifacts_dir,
        ),
        runtime=RuntimeConfig(
            module_name=str(runtime_raw.get("module_name", "generated_module")),
            fallback_to_deterministic=bool(
                runtime_raw.get("fallback_to_deterministic", True)
            ),
        ),
    )
