import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.scanner.project_scanner import analyze_project


app = FastAPI(
    title="OSS Compliance AI API",
    description="AI-enabled open-source license compliance scanner",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


REPORT_PATH = Path("outputs/compliance_report.csv")
SUMMARY_PATH = Path("outputs/project_summary.json")
EXCEL_PATH = Path("outputs/compliance_report.xlsx")
PDF_PATH = Path("outputs/compliance_report.pdf")


class ScanRequest(BaseModel):
    project_path: str


def is_github_url(value: str):
    try:
        parsed = urlparse(value)
        return parsed.scheme in ["http", "https"] and parsed.netloc == "github.com"
    except Exception:
        return False


def clone_github_repo(repo_url: str):
    temp_dir = tempfile.mkdtemp(prefix="oss_scan_")

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            check=True,
            capture_output=True,
            text=True,
        )

        return temp_dir

    except subprocess.CalledProcessError as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Git clone failed: {e.stderr}")


@app.get("/")
def root():
    return {
        "message": "OSS Compliance AI API is running",
        "endpoints": [
            "/scan",
            "/summary",
            "/report",
            "/download/excel",
        ],
    }


@app.post("/scan")
def scan_project(request: ScanRequest):
    scan_target = request.project_path
    temp_dir = None

    try:
        if is_github_url(scan_target):
            temp_dir = clone_github_repo(scan_target)
            scan_target = temp_dir

        report_info = analyze_project(scan_target)

        return {
            "status": "success",
            "input": request.project_path,
            "scanned_path": scan_target,
            "json_report": report_info["json_report"],
            "csv_report": report_info["csv_report"],
            "summary_report": report_info["summary_report"],
            "excel_report": report_info.get("excel_report"),
            "pdf_report": report_info.get("pdf_report"),
            "overall_project_risk": report_info["summary"]["overall_project_risk"],
            "summary": report_info["summary"],
            "results": report_info["results"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/summary")
def get_summary():
    if not SUMMARY_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Summary report not found. Run /scan first.",
        )

    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/report")
def get_report():
    if not REPORT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Compliance report not found. Run /scan first.",
        )

    df = pd.read_csv(REPORT_PATH)

    return df.to_dict(orient="records")


@app.get("/download/excel")
def download_excel_report():
    if not EXCEL_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Excel report not found. Run /scan first.",
        )

    return FileResponse(
        path=EXCEL_PATH,
        filename="compliance_report.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
@app.get("/download/pdf")
def download_pdf_report():
    if not PDF_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF report not found. Run /scan first.",
        )

    return FileResponse(
        path=PDF_PATH,
        filename="compliance_report.pdf",
        media_type="application/pdf",
    )