"""
Medicine loading and fuzzy-matching service.

The CSV is read once at startup (or on first use) and kept in memory as a
list of dicts plus a parallel list of normalized names, so every search
request only does an in-memory fuzzy comparison instead of touching disk.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from rapidfuzz import fuzz, process

from backend import config
from backend.utils.text_normalizer import (
    normalize_text,
    extract_medicine_name_candidate,
    parse_strength_and_form,
)  # normalize_text is also used directly in search() for the full-query variant

logger = logging.getLogger("medicine_matcher")


class MedicineNotLoadedError(Exception):
    """Raised when a search is attempted before / without a loaded CSV."""


class MedicineMatcher:
    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = Path(csv_path) if csv_path else config.MEDICINE_CSV_PATH
        self._records: list[dict] = []
        self._normalized_names: list[str] = []
        self._loaded = False
        self._columns_detected: dict[str, Optional[str]] = {}

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load(self) -> None:
        """Load the CSV into memory. Safe to call once at startup."""
        if not self.csv_path.exists():
            logger.error("Medicine CSV not found at %s", self.csv_path)
            self._loaded = False
            return

        try:
            df = pd.read_csv(self.csv_path, dtype=str, encoding="utf-8-sig")
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Failed to read medicine CSV: %s", exc)
            self._loaded = False
            return

        df.columns = [str(c).strip() for c in df.columns]
        lower_cols = {c.lower(): c for c in df.columns}

        name_col = self._pick_column(lower_cols, config.MEDICINE_NAME_COLUMNS)
        if name_col is None:
            # Fall back to the first column if nothing matches known names.
            name_col = df.columns[0]
            logger.warning(
                "No recognized medicine-name column found; falling back to "
                "first column '%s'",
                name_col,
            )

        generic_col = self._pick_column(lower_cols, config.GENERIC_NAME_COLUMNS)
        strength_col = self._pick_column(lower_cols, config.STRENGTH_COLUMNS)
        form_col = self._pick_column(lower_cols, config.FORM_COLUMNS)

        self._columns_detected = {
            "medicine_name": name_col,
            "generic_name": generic_col,
            "strength": strength_col,
            "form": form_col,
        }

        records = []
        normalized_names = []
        for _, row in df.iterrows():
            name = str(row.get(name_col, "")).strip()
            if not name or name.lower() == "nan":
                continue
            strength = self._clean(row.get(strength_col)) if strength_col else None
            form = self._clean(row.get(form_col)) if form_col else None
            if strength is None or form is None:
                # The catalog has no dedicated strength/form columns (common
                # for CSVs that combine everything into one name, e.g.
                # "A-Flox 250 mg Capsules") — fall back to parsing them out.
                guessed_strength, guessed_form = parse_strength_and_form(name)
                strength = strength or guessed_strength
                form = form or guessed_form

            record = {
                "medicine_name": name,
                "generic_name": self._clean(row.get(generic_col)) if generic_col else None,
                "strength": strength,
                "form": form,
            }
            records.append(record)
            normalized_names.append(normalize_text(name))

        self._records = records
        self._normalized_names = normalized_names
        self._loaded = True
        logger.info(
            "Loaded %d medicines from %s (columns detected: %s)",
            len(records),
            self.csv_path,
            self._columns_detected,
        )

    @staticmethod
    def _pick_column(lower_cols: dict, candidates: list[str]) -> Optional[str]:
        for candidate in candidates:
            if candidate in lower_cols:
                return lower_cols[candidate]
        return None

    @staticmethod
    def _clean(value) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text.lower() == "nan":
            return None
        return text

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def detected_columns(self) -> dict:
        return self._columns_detected

    def count(self) -> int:
        return len(self._records)

    # ------------------------------------------------------------------
    # Searching
    # ------------------------------------------------------------------
    def search(
        self,
        query: str,
        min_score: int = None,
        max_results: int = None,
    ) -> list[dict]:
        if not self._loaded:
            raise MedicineNotLoadedError(
                "medicine.csv is not loaded. Check the backend configuration."
            )

        min_score = config.MATCH_MIN_SCORE if min_score is None else min_score
        max_results = config.MATCH_MAX_RESULTS if max_results is None else max_results

        # Two query variants are matched against every candidate name and the
        # better of the two scores is kept:
        #  - the FULL normalized query (keeps strength/form words like
        #    "1 mg", "tablets") so that e.g. "Azolex 1 mg Tablets" ranks
        #    strictly above "Azolex 0.5 mg Tablets" instead of tying with it.
        #  - the STRIPPED name-only query (dosage/frequency words removed)
        #    so voice input like "Panadol 500 mg twice daily" still matches
        #    "Panadol 500mg Tablets" even though "twice daily" never appears
        #    in the catalog.
        full_query = normalize_text(query)
        stripped_query = extract_medicine_name_candidate(query)
        if not full_query and not stripped_query:
            return []

        full_matches = {
            idx: score
            for _, score, idx in process.extract(
                full_query,
                self._normalized_names,
                scorer=fuzz.WRatio,
                limit=max_results * 3,
            )
        } if full_query else {}

        stripped_matches = {
            idx: score
            for _, score, idx in process.extract(
                stripped_query,
                self._normalized_names,
                scorer=fuzz.WRatio,
                limit=max_results * 3,
            )
        } if stripped_query else {}

        combined_scores = {}
        for idx in set(full_matches) | set(stripped_matches):
            combined_scores[idx] = max(
                full_matches.get(idx, 0), stripped_matches.get(idx, 0)
            )

        ranked = sorted(combined_scores.items(), key=lambda kv: kv[1], reverse=True)

        results = []
        seen_names = set()
        for idx, score in ranked:
            if score < min_score:
                continue
            record = self._records[idx]
            key = record["medicine_name"].lower()
            if key in seen_names:
                continue
            seen_names.add(key)

            results.append({**record, "match_score": round(float(score), 1)})
            if len(results) >= max_results:
                break

        results.sort(key=lambda r: r["match_score"], reverse=True)
        return results

    def list_all(self, limit: int = 200) -> list[dict]:
        return self._records[:limit]


# Single shared instance, loaded once at application startup.
medicine_matcher = MedicineMatcher()
