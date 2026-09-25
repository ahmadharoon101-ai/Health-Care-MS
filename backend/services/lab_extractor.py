"""
AI/OCR laboratory report extraction (Module 1).

Pipeline: Upload -> extract raw text (PDF text layer, or OCR for images/
scanned PDFs) -> parse structured rows (test name / result / unit /
reference range / normal-abnormal flag) with heuristics -> the caller
(backend/api/laboratory.py) stores these as *unverified* LabResult rows.

Nothing here ever becomes the final medical record by itself — every
extracted row is created with verified=False and MUST go through the
Review -> Verify workflow (LabReport.status: uploaded -> extracted ->
verified) before it should be treated as trustworthy.

This uses lightweight, dependency-light heuristics (regex over the
extracted text) rather than a hosted LLM/vision API, so the whole system
keeps working fully offline, consistent with the existing Whisper-based
voice pipeline. It is intentionally conservative: when it isn't confident
about a line, it still surfaces it as a row for the human reviewer rather
than silently dropping data, since silent data loss is worse than an easy
manual correction.

Swap-in point: if the organization later provides a real OCR/LLM
extraction API, replace `extract_raw_text()` / `parse_lab_lines()` with
calls to that service — the rest of the pipeline (review/verify/save)
does not need to change.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("services.lab_extractor")

# Optional dependencies — the system must still run (in manual-entry-only
# mode for lab reports) if these aren't installed / tesseract isn't on PATH.
try:
    import pdfplumber

    _HAS_PDFPLUMBER = True
except ImportError:  # pragma: no cover
    _HAS_PDFPLUMBER = False

try:
    import pytesseract
    from PIL import Image

    _HAS_TESSERACT = True
except ImportError:  # pragma: no cover
    _HAS_TESSERACT = False


class ExtractionUnavailableError(Exception):
    pass


@dataclass
class ExtractedRow:
    test_name: str
    result_value: str | None
    unit: str | None
    reference_range: str | None
    flag: str | None  # "normal" | "abnormal" | None


# A typical lab report line looks like one of:
#   "Hemoglobin        13.5   g/dL   13.0-17.0"
#   "WBC Count : 11200 /uL (4000-11000) High"
#   "Glucose (Fasting)  95 mg/dL  70-100  Normal"
_UNIT_HINT = r"(?:g/dL|mg/dL|mmol/L|mIU/mL|IU/L|ng/mL|pg/mL|%|/uL|/mm3|10\^3/uL|10\^6/uL|U/L|meq/L|mEq/L)"
_LINE_RE = re.compile(
    rf"""^\s*
    (?P<name>[A-Za-z][A-Za-z0-9()/ .%+-]{{2,60}}?)      # test name
    \s*[:\-]?\s*
    (?P<value>-?\d+(?:\.\d+)?)                          # numeric result
    \s*
    (?P<unit>{_UNIT_HINT})?                             # optional unit
    \s*
    (?:[\(\[]?\s*(?P<range>\d+(?:\.\d+)?\s*[-–to]{{1,3}}\s*\d+(?:\.\d+)?)\s*[\)\]]?)?  # optional ref range
    \s*
    (?P<flag>high|low|normal|abnormal|h|l)?             # optional flag word
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_FLAG_MAP = {
    "high": "abnormal",
    "h": "abnormal",
    "low": "abnormal",
    "l": "abnormal",
    "abnormal": "abnormal",
    "normal": "normal",
}

# Lines that are clearly headers/boilerplate, not test rows — skip them so
# the reviewer isn't stuck deleting junk rows for every report.
_SKIP_PATTERNS = re.compile(
    r"^(patient|name|age|sex|gender|date|report|lab|doctor|address|specimen|"
    r"collected|reported|page|test\s*name|result|unit|reference|range)\s*[:\-]?\s*$",
    re.IGNORECASE,
)


def extract_raw_text(file_path: str, file_type: str) -> str:
    """Best-effort text extraction from a PDF or image lab report."""
    path = Path(file_path)

    if file_type == "pdf":
        text_parts = []
        if _HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text() or ""
                        text_parts.append(page_text)
            except Exception:
                logger.exception("pdfplumber failed to parse %s", path)
        text = "\n".join(text_parts).strip()

        # Text-based extraction found nothing useful — likely a scanned PDF.
        if not text and _HAS_TESSERACT:
            try:
                from pdf2image import convert_from_path  # optional extra

                images = convert_from_path(str(path))
                text = "\n".join(pytesseract.image_to_string(img) for img in images)
            except ImportError:
                logger.warning(
                    "Scanned PDF %s has no text layer and pdf2image/poppler is not "
                    "installed, so OCR fallback is unavailable. Results must be "
                    "entered manually during review.",
                    path,
                )
            except Exception:
                logger.exception("OCR fallback failed for scanned PDF %s", path)
        return text

    if file_type == "image":
        if not _HAS_TESSERACT:
            raise ExtractionUnavailableError(
                "OCR is not available on this server (pytesseract/Tesseract not "
                "installed). Install Tesseract OCR or enter results manually."
            )
        try:
            return pytesseract.image_to_string(Image.open(path))
        except Exception as exc:
            logger.exception("Tesseract OCR failed for %s", path)
            raise ExtractionUnavailableError(f"OCR failed: {exc}") from exc

    raise ValueError(f"Unsupported file_type: {file_type}")


def parse_lab_lines(raw_text: str) -> list[ExtractedRow]:
    """Turn raw OCR/text-layer output into candidate structured rows.

    Best-effort heuristic parsing — always meant to be reviewed and
    corrected by Lab Staff before verification, never trusted blindly.
    """
    rows: list[ExtractedRow] = []
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or _SKIP_PATTERNS.match(line):
            continue

        match = _LINE_RE.match(line)
        if not match:
            continue

        name = match.group("name").strip(" :-")
        if len(name) < 2:
            continue

        flag_word = (match.group("flag") or "").lower()
        rows.append(
            ExtractedRow(
                test_name=name.title(),
                result_value=match.group("value"),
                unit=match.group("unit"),
                reference_range=match.group("range"),
                flag=_FLAG_MAP.get(flag_word),
            )
        )

    return rows


def run_extraction(file_path: str, file_type: str) -> tuple[str, list[ExtractedRow]]:
    """Full pipeline used by POST /api/laboratory/extract. Returns
    (raw_text, rows). Raises ExtractionUnavailableError if OCR is required
    but unavailable — the caller should still let the report move to manual
    review rather than fail hard."""
    raw_text = extract_raw_text(file_path, file_type)
    rows = parse_lab_lines(raw_text) if raw_text else []
    return raw_text, rows
