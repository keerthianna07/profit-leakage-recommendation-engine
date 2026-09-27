import pandas as pd
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path


# -------------------------------------------------
# PROJECT PATHS
# -------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent
UI_DIR = BACKEND_DIR.parent
PROJECT_ROOT = UI_DIR.parent

UPLOAD_DIR = BACKEND_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAIN_SCRIPT = PROJECT_ROOT / "main_improve.py"


# -------------------------------------------------
# TRAINING STATUS
# -------------------------------------------------

status = {
    "running": False,
    "completed": False,
    "error": None,

    "stage": "Waiting to start",
    "progress": 0,

    "epoch": 0,
    "total_epochs": 50,

    "training_loss": None,
    "validation_loss": None,
    "learning_rate": None,

    "elapsed_seconds": 0,

    "threshold": None,
    "anomalies": None,
    "priority_customers": None,
    "critical_customers": None,

    "best_epoch": None,

    "logs": []
}


status_lock = threading.Lock()


# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def update_status(**kwargs):
    with status_lock:
        status.update(kwargs)


def add_log(message):
    with status_lock:
        status["logs"].append(message)

        # Keep memory usage small
        if len(status["logs"]) > 200:
            status["logs"] = status["logs"][-200:]


def get_status():
    with status_lock:
        return dict(status)


def reset_status():
    with status_lock:
        status.update({
            "running": False,
            "completed": False,
            "error": None,

            "stage": "Waiting to start",
            "progress": 0,

            "epoch": 0,
            "total_epochs": 50,

            "training_loss": None,
            "validation_loss": None,
            "learning_rate": None,

            "elapsed_seconds": 0,

            "threshold": None,
            "anomalies": None,
            "priority_customers": None,
            "critical_customers": None,

            "best_epoch": None,

            "logs": []
        })


# -------------------------------------------------
# PARSE TRAINING OUTPUT
# -------------------------------------------------

def process_output_line(line):
    line = line.strip()

    if not line:
        return

    add_log(line)

    # ---------------------------------------------
    # DATA LOADING
    # ---------------------------------------------

    if "Dataset loaded successfully" in line:
        update_status(
            stage="Data Loading",
            progress=5
        )

    # ---------------------------------------------
    # FEATURE ENGINEERING
    # ---------------------------------------------

    elif "Model feature count:" in line:
        update_status(
            stage="Feature Engineering",
            progress=12
        )

    # ---------------------------------------------
    # DATA PREPARATION
    # ---------------------------------------------

    elif "Training rows:" in line:
        update_status(
            stage="Data Preparation",
            progress=18
        )

    elif "Scaling completed!" in line:
        update_status(
            stage="Data Preparation",
            progress=25
        )

    # ---------------------------------------------
    # EPOCH OUTPUT
    # ---------------------------------------------

    elif re.search(r"Epoch\s+\d+/(\d+)", line):

        match = re.search(
            r"Epoch\s+(\d+)/(\d+)",
            line
        )

        if match:
            epoch = int(match.group(1))
            total_epochs = int(match.group(2))

            update_status(
                stage="Autoencoder Training",
                epoch=epoch,
                total_epochs=total_epochs,
                progress=25 + int((epoch / total_epochs) * 45)
            )

    # ---------------------------------------------
    # LOSS OUTPUT
    # ---------------------------------------------

    elif "loss:" in line and "val_loss:" in line:

        loss_match = re.search(
            r"loss:\s*([0-9.eE+-]+)",
            line
        )

        val_loss_match = re.search(
            r"val_loss:\s*([0-9.eE+-]+)",
            line
        )

        lr_match = re.search(
            r"learning_rate:\s*([0-9.eE+-]+)",
            line
        )

        update_kwargs = {}

        if loss_match:
            update_kwargs["training_loss"] = float(
                loss_match.group(1)
            )

        if val_loss_match:
            update_kwargs["validation_loss"] = float(
                val_loss_match.group(1)
            )

        if lr_match:
            update_kwargs["learning_rate"] = float(
                lr_match.group(1)
            )

        if update_kwargs:
            update_status(**update_kwargs)

    # ---------------------------------------------
    # ANOMALY DETECTION
    # ---------------------------------------------

    elif "Reconstruction error calculated" in line:
        update_status(
            stage="Anomaly Detection",
            progress=72
        )

    elif "95th percentile threshold:" in line:

        match = re.search(
            r"95th percentile threshold:\s*([0-9.eE+-]+)",
            line
        )

        if match:
            update_status(
                threshold=float(match.group(1))
            )

    elif "Anomalies detected:" in line:

        match = re.search(
            r"Anomalies detected:\s*(\d+)",
            line
        )

        if match:
            update_status(
                anomalies=int(match.group(1))
            )

    # ---------------------------------------------
    # CUSTOMER / RISK
    # ---------------------------------------------

    elif "CUSTOMER PROFIT-LEAKAGE PROFILE" in line:
        update_status(
            stage="Risk Scoring",
            progress=78
        )

    elif "Customers with anomalies:" in line:

        match = re.search(
            r"Customers with anomalies:\s*(\d+)",
            line
        )

        if match:
            update_status(
                priority_customers=int(match.group(1))
            )


    elif "Risk category distribution:" in line:

        update_status(

            stage="Risk Scoring",

            progress=83

        )



    elif re.search(r"^\s*CRITICAL\s+(\d+)", line):

        match = re.search(

            r"^\s*CRITICAL\s+(\d+)",

            line

        )

        if match:
            update_status(

                critical_customers=int(match.group(1))

            )

    # ---------------------------------------------
    # RECOMMENDATIONS
    # ---------------------------------------------

    elif "LEAKAGE PATTERN ANALYSIS" in line:
        update_status(
            stage="Recommendations",
            progress=88
        )

    elif "RECOMMENDATION ENGINE" in line:
        update_status(
            stage="Recommendations",
            progress=91
        )

    # ---------------------------------------------
    # BUSINESS SIMULATION
    # ---------------------------------------------

    elif "6-MONTH BUSINESS IMPACT SIMULATION" in line:
        update_status(
            stage="Business Simulation",
            progress=94
        )

    # ---------------------------------------------
    # COMPLETION
    # ---------------------------------------------

    elif "FINAL FILES EXPORTED" in line:
        update_status(
            stage="Completed",
            progress=100
        )


# -------------------------------------------------
# TRAINING PROCESS
# -------------------------------------------------

def run_training(dataset_path: str):

    reset_status()

    update_status(
        running=True,
        stage="Starting training",
        progress=1
    )

    start_time = time.time()

    try:

        dataset = Path(dataset_path)

        if not dataset.exists():
            raise FileNotFoundError(
                f"Dataset not found: {dataset}"
            )

        if not MAIN_SCRIPT.exists():
            raise FileNotFoundError(
                f"Training script not found: {MAIN_SCRIPT}"
            )

        # -----------------------------------------
        # Environment variable tells main_improve.py
        # which dataset to load.
        # -----------------------------------------

        env = os.environ.copy()

        env["TRAINING_DATASET"] = str(
            dataset.resolve()
        )

        # -----------------------------------------
        # Launch actual ML pipeline
        # -----------------------------------------

        process = subprocess.Popen(
            [
                sys.executable,
                str(MAIN_SCRIPT)
            ],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            bufsize=1,
            env={
                **env,
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1"
            }
        )

        # -----------------------------------------
        # Read output live
        # -----------------------------------------

        for raw_line in process.stdout:

            line = raw_line.decode(
                "utf-8",
                errors="replace"
            ).strip()

            if line:
                process_output_line(line)

            update_status(
                elapsed_seconds=int(
                    time.time() - start_time
                )
            )

        process.wait()

        # -----------------------------------------
        # Process finished
        # -----------------------------------------

        if process.returncode != 0:
            raise RuntimeError(
                f"Training process exited with "
                f"code {process.returncode}"
            )

        # -----------------------------------------
        # READ FINAL MODEL RESULTS
        # -----------------------------------------

        output_file = PROJECT_ROOT / "dashboard_data_improved.csv"

        if output_file.exists():

            results_df = pd.read_csv(output_file)

            if "Risk_Category" in results_df.columns:
                critical_count = int(
                    (results_df["Risk_Category"] == "CRITICAL").sum()
                )

                priority_count = len(results_df)

                update_status(
                    critical_customers=critical_count,
                    priority_customers=priority_count
                )

        update_status(
            running=False,
            completed=True,
            stage="Completed",
            progress=100,
            elapsed_seconds=int(
                time.time() - start_time
            )
        )

    except Exception as exc:

        update_status(
            running=False,
            completed=False,
            error=str(exc),
            stage="Training failed",
            progress=0
        )

        add_log(
            f"ERROR: {exc}"
        )


# -------------------------------------------------
# START TRAINING IN BACKGROUND
# -------------------------------------------------

def start_training(dataset_path: str):

    with status_lock:

        if status["running"]:
            return False

        status["running"] = True

    thread = threading.Thread(
        target=run_training,
        args=(dataset_path,),
        daemon=True
    )

    thread.start()

    return True