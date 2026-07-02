"""
VyapaarScore — FastAPI Backend
Exposes the UPI cash-flow scoring engine as a REST API.
"""

import os
import tempfile
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from score_engine import score_merchant, compute_score_trend
from tips_engine import generate_tips, generate_strength

app = FastAPI(
    title="VyapaarScore API",
    description="UPI Cash-Flow Digital Footprint Scoring Engine",
    version="0.1.0",
)

# Allow CORS for future frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok"}


@app.post("/score")
async def score_csv(file: UploadFile = File(...)):
    """
    Accept a CSV upload of UPI transactions and return the
    merchant trust score produced by score_merchant().

    The CSV must have columns: transaction_id, timestamp, amount,
    type (credit/debit), status (success/failed), payer_vpa, payee_vpa.
    """
    # Validate file type
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only .csv files are accepted.",
        )

    # Write upload to a temp file so score_merchant() can read it by path
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(tmp_fd, "wb") as tmp:
            shutil.copyfileobj(file.file, tmp)

        result = score_merchant(tmp_path)
        result["tips"] = generate_tips(result["factors_normalized_0_1"], result["factor_details"])
        result["strength"] = generate_strength(result["factors_normalized_0_1"], result["factor_details"])
        result["trend"] = compute_score_trend(tmp_path)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to score the uploaded CSV: {str(e)}",
        )
    finally:
        # Clean up the temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
