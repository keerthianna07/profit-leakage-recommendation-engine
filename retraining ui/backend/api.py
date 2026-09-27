import shutil
import uuid
import pandas as pd

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException
)

from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parents[2]

from .trainer import (
    UPLOAD_DIR,
    get_status,
    start_training
)


# -------------------------------------------------
# PATHS
# -------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent
UI_DIR = BACKEND_DIR.parent
FRONTEND_DIR = UI_DIR / "frontend"


# -------------------------------------------------
# FASTAPI APP
# -------------------------------------------------

app = FastAPI(
    title="Profit Leakage Retraining API",
    version="1.0"
)


# -------------------------------------------------
# CORS
# -------------------------------------------------

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# -------------------------------------------------
# FRONTEND
# -------------------------------------------------

app.mount(
    "/frontend",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True
    ),
    name="frontend"
)


# -------------------------------------------------
# ROOT
# -------------------------------------------------

@app.get("/")
def root():

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# -------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------

@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "service": "profit leakage retraining"
    }


# -------------------------------------------------
# STATUS
# -------------------------------------------------

@app.get("/api/status")
def training_status():

    return get_status()


# -------------------------------------------------
# UPLOAD DATASET
# -------------------------------------------------

@app.post("/api/upload")
async def upload_dataset(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    allowed_extensions = {
        ".xlsx",
        ".xls",
        ".csv"
    }

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only XLSX, XLS, and CSV files are supported"
        )

    unique_name = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    destination = (
        UPLOAD_DIR /
        unique_name
    )

    with destination.open("wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    return {
        "message": "Dataset uploaded successfully",
        "filename": file.filename,
        "path": str(destination)
    }


# -------------------------------------------------
# START TRAINING
# -------------------------------------------------

@app.post("/api/train")
def start_training_endpoint(
    dataset_path: str
):

    started = start_training(
        dataset_path
    )

    if not started:

        raise HTTPException(
            status_code=409,
            detail="Training is already running"
        )

    return {
        "message": "Training started"
    }

@app.get("/api/recommendations")
def get_recommendations():
    """Return the latest customer recommendations from the retraining run."""

    output_file = PROJECT_ROOT / "dashboard_data_improved.csv"

    if not output_file.exists():
        raise HTTPException(
            status_code=404,
            detail="No retraining recommendation output is available yet."
        )

    try:
        df = pd.read_csv(output_file)

        required_columns = [
            "Customer ID",
            "Risk_Score",
            "Risk_Category",
            "Potential_Loss",
            "Leakage_Pattern",
            "Primary_Driver",
            "Recommendation",
            "Recommendation_Priority",
        ]

        missing = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Recommendation output is missing required columns: "
                    + ", ".join(missing)
                ),
            )

        recommendations = (
            df[required_columns]
            .sort_values(
                by="Risk_Score",
                ascending=False
            )
            .head(20)
            .to_dict(orient="records")
        )

        for row in recommendations:
            for key, value in row.items():
                if pd.isna(value):
                    row[key] = None

        return {
            "count": len(recommendations),
            "recommendations": recommendations,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load recommendations: {exc}"
        )
