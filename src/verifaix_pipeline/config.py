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
    max_tokens: int
    use_llm_for_testplan: bool
    use_llm_for_code: bool
    use_llm_for_tests: bool


@dataclass(frozen=True)
class StorageConfig:
    database_path: Path
    artifacts_dir: Path


@dataclass(frozen=True)
class ExtractionConfig:
    use_ocr: bool
    ocr_mode: str
    min_text_chars: int
    ocr_dpi: int
    use_vision_for_images: bool
    vision_mode: str
    max_vision_pages: int
    vision_dpi: int


@dataclass(frozen=True)
class RuntimeConfig:
    module_name: str
    fallback_to_deterministic: bool


@dataclass(frozen=True)
class AppConfig:
    llm: LLMConfig
    storage: StorageConfig
    extraction: ExtractionConfig
    runtime: RuntimeConfig


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    llm_raw = raw.get("llm", {})
    storage_raw = raw.get("storage", {})
    extraction_raw = raw.get("extraction", {})
    runtime_raw = raw.get("runtime", {})

    base_dir = config_path.parent
    database_path = Path(storage_raw.get("database_path", "verifaix.db"))
    artifacts_dir = Path(storage_raw.get("artifacts_dir", "artifacts"))
    if not database_path.is_absolute():
        database_path = base_dir / database_path
    if not artifacts_dir.is_absolute():
        artifacts_dir = base_dir / artifacts_dir

    provider = str(llm_raw.get("llm_provider", "none")).lower()
    if provider not in {"none", "openai", "anthropic"}:
        raise ValueError(f"Unsupported llm_provider: {provider}")

    ocr_mode = str(extraction_raw.get("ocr_mode", "auto")).lower()
    if ocr_mode not in {"auto", "always", "never"}:
        raise ValueError(f"Unsupported ocr_mode: {ocr_mode}")
    vision_mode = str(extraction_raw.get("vision_mode", "auto")).lower()
    if vision_mode not in {"auto", "always", "never"}:
        raise ValueError(f"Unsupported vision_mode: {vision_mode}")

    return AppConfig(
        llm=LLMConfig(
            llm_provider=provider,
            model_name=str(llm_raw.get("model_name", "")),
            api_key_env=str(llm_raw.get("api_key_env", "")),
            temperature=float(llm_raw.get("temperature", 0.0)),
            max_tokens=int(llm_raw.get("max_tokens", 8192)),
            use_llm_for_testplan=bool(llm_raw.get("use_llm_for_testplan", False)),
            use_llm_for_code=bool(llm_raw.get("use_llm_for_code", False)),
            use_llm_for_tests=bool(llm_raw.get("use_llm_for_tests", False)),
        ),
        storage=StorageConfig(
            database_path=database_path,
            artifacts_dir=artifacts_dir,
        ),
        extraction=ExtractionConfig(
            use_ocr=bool(extraction_raw.get("use_ocr", False)),
            ocr_mode=ocr_mode,
            min_text_chars=int(extraction_raw.get("min_text_chars", 200)),
            ocr_dpi=int(extraction_raw.get("ocr_dpi", 200)),
            use_vision_for_images=bool(
                extraction_raw.get("use_vision_for_images", False)
            ),
            vision_mode=vision_mode,
            max_vision_pages=int(extraction_raw.get("max_vision_pages", 4)),
            vision_dpi=int(extraction_raw.get("vision_dpi", 150)),
        ),
        runtime=RuntimeConfig(
            module_name=str(runtime_raw.get("module_name", "generated_module")),
            fallback_to_deterministic=bool(
                runtime_raw.get("fallback_to_deterministic", True)
            ),
        ),
    )
