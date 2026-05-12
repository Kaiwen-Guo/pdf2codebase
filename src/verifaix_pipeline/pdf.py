from __future__ import annotations

from base64 import b64encode
from hashlib import sha256
from pathlib import Path
import json
import re
import shutil
import subprocess
import tempfile
from typing import Any
from urllib import request

from .models import Description

DEFAULT_VISION_PROMPT = (
    "Inspect this rendered PDF page for software requirements that may be "
    "expressed in diagrams, screenshots, tables, flowcharts, or embedded images. "
    "Return concise English notes only when they affect APIs, behavior, edge cases, "
    "errors, data flow, or constraints. If there is no relevant visual information, "
    "return 'No relevant visual requirements found.'"
)


def extract_description(
    path: str | Path,
    *,
    extraction_config: Any | None = None,
    llm_config: Any | None = None,
) -> Description:
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    text = _extract_text(input_path, extraction_config, llm_config)
    normalized = normalize_text(text)
    return Description(
        pdf_path=str(input_path),
        text=normalized,
        text_hash=sha256(normalized.encode("utf-8")).hexdigest(),
    )


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def extract_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^(\d+(?:\.\d+)*)\s+([^\n]+)$", text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        section_id = match.group(1)
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[section_id] = text[start:end].strip()
    return sections


def _extract_text(
    path: Path,
    extraction_config: Any | None = None,
    llm_config: Any | None = None,
) -> str:
    if path.suffix.lower() == ".pdf":
        return _extract_pdf_text(path, extraction_config, llm_config)
    if path.suffix.lower() in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported description file type: {path.suffix}")


def _extract_pdf_text(
    path: Path,
    extraction_config: Any | None = None,
    llm_config: Any | None = None,
) -> str:
    native_text = _extract_pdf_native_text(path)
    parts = [native_text]
    if _should_run_visual_layer(
        native_text,
        bool(getattr(extraction_config, "use_ocr", False)),
        str(getattr(extraction_config, "ocr_mode", "auto")),
        int(getattr(extraction_config, "min_text_chars", 200)),
    ):
        ocr_text = _extract_pdf_ocr_text(
            path, int(getattr(extraction_config, "ocr_dpi", 200))
        )
        if normalize_text(ocr_text):
            parts.append("[OCR EXTRACTED TEXT]\n" + ocr_text)

    if _should_run_visual_layer(
        native_text,
        bool(getattr(extraction_config, "use_vision_for_images", False)),
        str(getattr(extraction_config, "vision_mode", "auto")),
        int(getattr(extraction_config, "min_text_chars", 200)),
    ):
        vision_text = _extract_pdf_visual_notes(
            path,
            llm_config,
            int(getattr(extraction_config, "max_vision_pages", 4)),
            int(getattr(extraction_config, "vision_dpi", 150)),
        )
        if normalize_text(vision_text):
            parts.append("[VISUAL PDF ANALYSIS]\n" + vision_text)
    return "\n\n".join(part for part in parts if normalize_text(part))


def _extract_pdf_native_text(path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        result = subprocess.run(
            [pdftotext, "-layout", str(path), "-"],
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout

    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PDF extraction requires pdftotext or the optional pypdf package"
        ) from exc

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _should_run_visual_layer(
    native_text: str,
    enabled: bool,
    mode: str,
    min_text_chars: int,
) -> bool:
    if not enabled or mode == "never":
        return False
    if mode == "always":
        return True
    return len(normalize_text(native_text)) < min_text_chars


def _extract_pdf_ocr_text(path: Path, dpi: int) -> str:
    pdftoppm = shutil.which("pdftoppm")
    tesseract = shutil.which("tesseract")
    if not pdftoppm or not tesseract:
        missing = [
            name
            for name, tool in [("pdftoppm", pdftoppm), ("tesseract", tesseract)]
            if not tool
        ]
        raise RuntimeError(
            "OCR extraction requires these command line tools: " + ", ".join(missing)
        )

    with tempfile.TemporaryDirectory(prefix="verifaix_ocr_") as tmp:
        prefix = Path(tmp) / "page"
        subprocess.run(
            [pdftoppm, "-png", "-r", str(dpi), str(path), str(prefix)],
            check=True,
            text=True,
            capture_output=True,
        )
        page_texts: list[str] = []
        for page_image in sorted(Path(tmp).glob("page-*.png")):
            result = subprocess.run(
                [tesseract, str(page_image), "stdout", "--psm", "6"],
                check=True,
                text=True,
                capture_output=True,
            )
            page_number = page_image.stem.rsplit("-", 1)[-1].lstrip("0") or "1"
            page_text = normalize_text(result.stdout)
            if page_text:
                page_texts.append(f"[OCR page {page_number}]\n{page_text}")
        return "\n\n".join(page_texts)


def _extract_pdf_visual_notes(
    path: Path,
    llm_config: Any | None,
    max_pages: int,
    dpi: int,
) -> str:
    if llm_config is None or getattr(llm_config, "llm_provider", "none") == "none":
        raise RuntimeError("Visual PDF analysis requires a configured LLM provider")
    provider = str(getattr(llm_config, "llm_provider", "none"))
    api_key_env = str(getattr(llm_config, "api_key_env", ""))
    if provider not in {"openai", "anthropic"}:
        raise RuntimeError(f"Visual PDF analysis does not support provider: {provider}")

    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("Visual PDF analysis requires pdftoppm")

    with tempfile.TemporaryDirectory(prefix="verifaix_vision_") as tmp:
        prefix = Path(tmp) / "page"
        subprocess.run(
            [
                pdftoppm,
                "-png",
                "-r",
                str(dpi),
                "-f",
                "1",
                "-l",
                str(max_pages),
                str(path),
                str(prefix),
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        notes: list[str] = []
        for page_image in sorted(Path(tmp).glob("page-*.png")):
            page_number = page_image.stem.rsplit("-", 1)[-1].lstrip("0") or "1"
            image_bytes = page_image.read_bytes()
            if provider == "openai":
                page_notes = _openai_visual_notes(image_bytes, llm_config, api_key_env)
            else:
                page_notes = _anthropic_visual_notes(
                    image_bytes, llm_config, api_key_env
                )
            page_notes = normalize_text(page_notes)
            if page_notes:
                notes.append(f"[Visual page {page_number}]\n{page_notes}")
        return "\n\n".join(notes)


def _openai_visual_notes(
    image_bytes: bytes,
    llm_config: Any,
    api_key_env: str,
) -> str:
    api_key = _api_key(api_key_env)
    body = json.dumps(
        {
            "model": getattr(llm_config, "model_name"),
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": DEFAULT_VISION_PROMPT},
                        {
                            "type": "input_image",
                            "image_url": "data:image/png;base64,"
                            + b64encode(image_bytes).decode("ascii"),
                        },
                    ],
                }
            ],
            "temperature": getattr(llm_config, "temperature", 0.0),
        }
    ).encode("utf-8")
    http_request = request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with request.urlopen(http_request, timeout=120) as response:
        raw = json.loads(response.read().decode("utf-8"))
    if "output_text" in raw:
        return str(raw["output_text"])
    chunks: list[str] = []
    for item in raw.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                chunks.append(str(content.get("text", "")))
    return "\n".join(chunks) if chunks else json.dumps(raw)


def _anthropic_visual_notes(
    image_bytes: bytes,
    llm_config: Any,
    api_key_env: str,
) -> str:
    api_key = _api_key(api_key_env)
    body = json.dumps(
        {
            "model": getattr(llm_config, "model_name"),
            "max_tokens": getattr(llm_config, "max_tokens", 4096),
            "temperature": getattr(llm_config, "temperature", 0.0),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": b64encode(image_bytes).decode("ascii"),
                            },
                        },
                        {"type": "text", "text": DEFAULT_VISION_PROMPT},
                    ],
                }
            ],
        }
    ).encode("utf-8")
    http_request = request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    with request.urlopen(http_request, timeout=120) as response:
        raw = json.loads(response.read().decode("utf-8"))
    chunks = [
        str(item.get("text", ""))
        for item in raw.get("content", [])
        if item.get("type") == "text"
    ]
    return "\n".join(chunks) if chunks else json.dumps(raw)


def _api_key(api_key_env: str) -> str:
    from os import environ

    api_key = environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing API key environment variable: {api_key_env}")
    return api_key
