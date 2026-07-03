"""Data-quality expectations and lightweight validation reporting."""

from pathlib import Path

import great_expectations as gx
import pandas as pd
from great_expectations.core.expectation_suite import ExpectationSuite

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_FILE = PROJECT_ROOT / "data" / "raw" / "patients_raw.csv"
VALID_CONDITIONS = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
IMPORTANT_COLUMNS = ["patient_id", "cccd", "benh", "ket_qua_xet_nghiem"]


def build_patient_expectation_suite() -> ExpectationSuite:
    """Create the six expectations specified by the lab assignment."""
    expectations = gx.expectations
    checks = [
        expectations.ExpectColumnValuesToNotBeNull(column="patient_id"),
        expectations.ExpectColumnValueLengthsToEqual(column="cccd", value=12),
        expectations.ExpectColumnValuesToBeBetween(
            column="ket_qua_xet_nghiem", min_value=0, max_value=50
        ),
        expectations.ExpectColumnValuesToBeInSet(
            column="benh", value_set=VALID_CONDITIONS
        ),
        expectations.ExpectColumnValuesToMatchRegex(
            column="email", regex=r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        ),
        expectations.ExpectColumnValuesToBeUnique(column="patient_id"),
    ]
    return gx.ExpectationSuite(name="patient_data_suite", expectations=checks)


def validate_anonymized_data(filepath: str) -> dict:
    """Validate privacy, required values, row count, and training constraints."""
    df = pd.read_csv(filepath, dtype={"cccd": str, "so_dien_thoai": str})
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {"total_rows": len(df), "columns": list(df.columns)},
    }

    missing_columns = [column for column in IMPORTANT_COLUMNS if column not in df]
    if missing_columns:
        results["failed_checks"].append(
            f"Missing required columns: {', '.join(missing_columns)}"
        )
    else:
        if RAW_DATA_FILE.exists() and "cccd" in pd.read_csv(
            RAW_DATA_FILE, nrows=0
        ).columns:
            original_cccd = set(
                pd.read_csv(RAW_DATA_FILE, dtype={"cccd": str})["cccd"].dropna()
            )
            leaked_cccd = original_cccd.intersection(df["cccd"].dropna().astype(str))
            if leaked_cccd:
                results["failed_checks"].append(
                    "CCCD column still contains values from the raw dataset"
                )
        if df[IMPORTANT_COLUMNS].isnull().any().any():
            results["failed_checks"].append("Important columns contain null values")
        if not df["benh"].isin(VALID_CONDITIONS).all():
            results["failed_checks"].append("Condition column contains invalid values")
        values = pd.to_numeric(df["ket_qua_xet_nghiem"], errors="coerce")
        if values.isna().any() or not values.between(0, 50).all():
            results["failed_checks"].append("Test results must be between 0 and 50")

    if RAW_DATA_FILE.exists():
        original_rows = len(pd.read_csv(RAW_DATA_FILE))
        results["stats"]["original_rows"] = original_rows
        if len(df) != original_rows:
            results["failed_checks"].append(
                f"Row count mismatch: expected {original_rows}, got {len(df)}"
            )
    else:
        results["failed_checks"].append("Original dataset is unavailable")

    results["success"] = not results["failed_checks"]
    return results
