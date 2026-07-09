"""
VyapaarScore — FastAPI Backend
Exposes the UPI cash-flow scoring engine as a REST API.
"""

import os
import tempfile
import shutil

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from score_engine import score_merchant, compute_score_trend, load_transactions
from tips_engine import generate_tips, generate_strength
from simulator import simulate
from anomaly_detector import check_integrity
from benchmarking import get_benchmark, list_categories
from lender_report import get_lender_recommendation, DECISION_LABELS

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


@app.get("/categories")
def get_categories():
    """Return the list of merchant categories for benchmarking."""
    return list_categories()


@app.post("/score")
async def score_csv(file: UploadFile = File(...), category: str = Form("general_service")):
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
        
        transactions = load_transactions(tmp_path)
        result["integrity"] = check_integrity(transactions)
        
        result["benchmark"] = get_benchmark(result["score"], category)
        
        lender_rec = get_lender_recommendation(
            result["score"], result["grade"], result["integrity"], result["benchmark"]
        )
        lender_rec["label"], lender_rec["tone"] = DECISION_LABELS[lender_rec["decision"]]
        result["lender_recommendation"] = lender_rec
        
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


@app.post("/score_demo")
async def score_demo(category: str = Form("general_service"), bank: str = Form("IDBI Bank")):
    """
    Simulated Account Aggregator endpoint.
    Scores the appropriate local CSV file for demonstration based on the selected bank.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        bank_to_file = {
            "IDBI Bank": "stable_kirana.csv",
            "HDFC Bank": "growing_shop.csv",
            "ICICI Bank": "seasonal_vendor.csv",
            "State Bank of India": "gaming_attempt.csv"
        }
        filename = bank_to_file.get(bank, "stable_kirana.csv")
        demo_file = os.path.join(base_dir, filename)
        
        result = score_merchant(demo_file)
        result["tips"] = generate_tips(result["factors_normalized_0_1"], result["factor_details"])
        result["strength"] = generate_strength(result["factors_normalized_0_1"], result["factor_details"])
        result["trend"] = compute_score_trend(demo_file)
        
        transactions = load_transactions(demo_file)
        result["integrity"] = check_integrity(transactions)
        
        result["benchmark"] = get_benchmark(result["score"], category)
        
        lender_rec = get_lender_recommendation(
            result["score"], result["grade"], result["integrity"], result["benchmark"]
        )
        lender_rec["label"], lender_rec["tone"] = DECISION_LABELS[lender_rec["decision"]]
        result["lender_recommendation"] = lender_rec
        
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to score the demo CSV: {str(e)}",
        )


@app.post("/simulate_demo")
async def simulate_demo_endpoint(
    bank: str = Form("IDBI Bank"),
    inflow_growth_pct: float = Form(0),
    new_repeat_customers: int = Form(0),
    reduce_failures_pct: float = Form(0),
    reduce_outflows_pct: float = Form(0),
):
    """
    Simulated Account Aggregator simulator endpoint.
    Runs the what-if simulator on the demo CSV file corresponding to the bank.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        bank_to_file = {
            "IDBI Bank": "stable_kirana.csv",
            "HDFC Bank": "growing_shop.csv",
            "ICICI Bank": "seasonal_vendor.csv",
            "State Bank of India": "gaming_attempt.csv"
        }
        filename = bank_to_file.get(bank, "stable_kirana.csv")
        demo_file = os.path.join(base_dir, filename)
        
        transactions = load_transactions(demo_file)
        result = simulate(
            transactions,
            inflow_growth_pct=inflow_growth_pct,
            new_repeat_customers=new_repeat_customers,
            reduce_failures_pct=reduce_failures_pct,
            reduce_outflows_pct=reduce_outflows_pct,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to simulate demo score: {str(e)}",
        )


@app.post("/simulate")
async def simulate_endpoint(
    file: UploadFile = File(...),
    inflow_growth_pct: float = Form(0),
    new_repeat_customers: int = Form(0),
    reduce_failures_pct: float = Form(0),
    reduce_outflows_pct: float = Form(0),
):
    """
    Accept a CSV upload and simulation parameters, run the simulator,
    and return the baseline and simulated scores.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only .csv files are accepted.",
        )

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(tmp_fd, "wb") as tmp:
            shutil.copyfileobj(file.file, tmp)
            
        transactions = load_transactions(tmp_path)
        result = simulate(
            transactions,
            inflow_growth_pct=inflow_growth_pct,
            new_repeat_customers=new_repeat_customers,
            reduce_failures_pct=reduce_failures_pct,
            reduce_outflows_pct=reduce_outflows_pct,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to simulate score: {str(e)}",
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
