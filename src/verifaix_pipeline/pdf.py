from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re
import shutil
import subprocess

from .models import Description


def extract_description(path: str | Path) -> Description:
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    text = _extract_text(input_path)
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


def _extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return _extract_pdf_text(path)
    if path.suffix.lower() in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported description file type: {path.suffix}")


def _extract_pdf_text(path: Path) -> str:
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
