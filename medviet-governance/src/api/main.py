"""FastAPI endpoints protected by the MedViet RBAC policy."""

from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException

from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()
DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "raw" / "patients_raw.csv"


def _load_patients() -> pd.DataFrame:
    if not DATA_FILE.exists():
        raise HTTPException(status_code=503, detail="Patient dataset is unavailable")
    return pd.read_csv(DATA_FILE, dtype={"cccd": str, "so_dien_thoai": str})


@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(current_user: dict = Depends(get_current_user)):
    """Return the first ten raw patient records (admin only)."""
    return _load_patients().head(10).to_dict(orient="records")


@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(current_user: dict = Depends(get_current_user)):
    """Return the first ten records after direct identifiers are replaced."""
    return anonymizer.anonymize_dataframe(_load_patients().head(10)).to_dict(
        orient="records"
    )


@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(current_user: dict = Depends(get_current_user)):
    """Return non-identifying patient counts grouped by condition."""
    counts = _load_patients()["benh"].value_counts(dropna=False)
    return {
        "total_patients": int(counts.sum()),
        "patients_by_condition": {str(key): int(value) for key, value in counts.items()},
    }


@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(patient_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a patient record; authorization is restricted to admins."""
    df = _load_patients()
    remaining = df[df["patient_id"].astype(str) != patient_id]
    if len(remaining) == len(df):
        raise HTTPException(status_code=404, detail="Patient not found")
    remaining.to_csv(DATA_FILE, index=False)
    return {"deleted": True, "patient_id": patient_id}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
