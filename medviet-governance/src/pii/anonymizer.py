"""PII anonymization helpers for text and patient dataframes."""

import secrets

import pandas as pd
from faker import Faker
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")


def _fake_cccd() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(12))


def _fake_phone() -> str:
    return f"0{secrets.choice('35789')}" + "".join(
        secrets.choice("0123456789") for _ in range(8)
    )


class MedVietAnonymizer:
    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    @staticmethod
    def _mask_detected_values(text: str, results: list) -> str:
        """Keep each word's first character and mask the remaining letters."""
        output = text
        for result in sorted(results, key=lambda item: item.start, reverse=True):
            value = output[result.start : result.end]
            masked = " ".join(
                word[:1] + "*" * max(0, len(word) - 1) for word in value.split(" ")
            )
            output = output[: result.start] + masked + output[result.end :]
        return output

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """Anonymize detected PII using replacement, masking, or SHA-256."""
        text = str(text)
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        if strategy == "mask":
            return self._mask_detected_values(text, results)
        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig(
                    "replace", {"new_value": fake.email()}
                ),
                "VN_CCCD": OperatorConfig("replace", {"new_value": _fake_cccd()}),
                "VN_PHONE": OperatorConfig("replace", {"new_value": _fake_phone()}),
            }
        elif strategy == "hash":
            operators = {
                "DEFAULT": OperatorConfig("hash", {"hash_type": "sha256"})
            }
        else:
            raise ValueError("strategy must be one of: replace, mask, hash")

        return self.anonymizer.anonymize(
            text=text, analyzer_results=results, operators=operators
        ).text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy with direct identifiers replaced by synthetic data."""
        df_anon = df.copy()
        replacements = {
            "ho_ten": lambda _value: fake.name(),
            "dia_chi": lambda _value: fake.address().replace("\n", ", "),
            "email": lambda _value: fake.email(),
            "cccd": lambda _value: _fake_cccd(),
            "so_dien_thoai": lambda _value: _fake_phone(),
            "ngay_sinh": lambda _value: fake.date_of_birth(
                minimum_age=18, maximum_age=90
            ).strftime("%d/%m/%Y"),
            "bac_si_phu_trach": lambda _value: fake.name(),
        }
        for column, replacement in replacements.items():
            if column in df_anon.columns:
                df_anon[column] = df_anon[column].map(replacement)
        return df_anon

    def calculate_detection_rate(self, original_df: pd.DataFrame, pii_columns: list) -> float:
        """Calculate the fraction of non-null PII cells detected by Presidio."""
        total = detected = 0
        for column in pii_columns:
            if column not in original_df.columns:
                raise ValueError(f"Unknown PII column: {column}")
            for value in original_df[column].dropna().astype(str):
                # CSV type inference can discard the leading zero of numeric
                # identifiers. Restore the documented widths for detection.
                if column == "cccd" and value.isdigit():
                    value = value.zfill(12)
                elif column == "so_dien_thoai" and value.isdigit():
                    value = value.zfill(10)
                total += 1
                detected += bool(detect_pii(value, self.analyzer))
        return detected / total if total else 0.0
