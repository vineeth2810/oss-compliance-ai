import json
import shutil
import subprocess
import tempfile
import tarfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
CYCLONEDX_SBOM_PATH = Path("outputs/sbom_cyclonedx.json")
SPDX_SBOM_PATH = Path("outputs/sbom_spdx.json")


class ScanRequest(BaseModel):
    project_path: str


def classify_input_source(value: str):
    value = value.strip()
    parsed = urlparse(value)

    if Path(value).exists():
        return "local_path"

    if parsed.scheme in ["http", "https", "git", "ssh"]:
        lower = value.lower()

        if lower.endswith((".zip", ".tar.gz", ".tgz")):
            return "archive_url"

        if (
            "github.com" in parsed.netloc
            or "gitlab.com" in parsed.netloc
            or "bitbucket.org" in parsed.netloc
            or lower.endswith(".git")
        ):
            return "git_repo"

        return "unsupported_url"

    return "unknown"


def clone_git_repo(repo_url: str):
    temp_dir = tempfile.mkdtemp(prefix="oss_git_scan_")

    try:
        print(f"Cloning repository: {repo_url}")

        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

        print("Clone completed.")
        return temp_dir

    except subprocess.TimeoutExpired:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError("Git clone timed out after 120 seconds.")

    except subprocess.CalledProcessError as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Git clone failed: {e.stderr}")


def download_archive(archive_url: str):
    temp_dir = tempfile.mkdtemp(prefix="oss_archive_scan_")
    archive_path = Path(temp_dir) / "archive"

    try:
        response = requests.get(archive_url, timeout=60)

        if response.status_code != 200:
            raise RuntimeError(
                f"Archive download failed with status {response.status_code}"
            )

        lower = archive_url.lower()

        if lower.endswith(".zip"):
            archive_path = archive_path.with_suffix(".zip")

        elif lower.endswith(".tar.gz"):
            archive_path = archive_path.with_suffix(".tar.gz")

        elif lower.endswith(".tgz"):
            archive_path = archive_path.with_suffix(".tgz")

        else:
            raise RuntimeError("Unsupported archive format")

        with open(archive_path, "wb") as f:
            f.write(response.content)

        extract_dir = Path(temp_dir) / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

        elif str(archive_path).endswith(".tar.gz") or str(archive_path).endswith(".tgz"):
            with tarfile.open(archive_path, "r:gz") as tar_ref:
                tar_ref.extractall(extract_dir)

        return str(extract_dir), temp_dir

    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def prepare_scan_target(input_value: str):
    source_type = classify_input_source(input_value)

    if source_type == "local_path":
        return input_value, None, source_type

    if source_type == "git_repo":
        temp_dir = clone_git_repo(input_value)
        return temp_dir, temp_dir, source_type

    if source_type == "archive_url":
        extract_dir, temp_dir = download_archive(input_value)
        return extract_dir, temp_dir, source_type

    if source_type == "unsupported_url":
        raise RuntimeError(
            "Unsupported URL. Provide a Git repository URL, GitHub/GitLab/Bitbucket URL, "
            "or a direct .zip/.tar.gz/.tgz archive URL."
        )

    raise RuntimeError(
        "Unsupported input. Provide a local project path, Git repository URL, or archive URL."
    )


@app.get("/")
def root():
    return {
        "message": "OSS Compliance AI API is running",
        "supported_inputs": [
            "local project path",
            "GitHub repository URL",
            "GitLab repository URL",
            "Bitbucket repository URL",
            "generic .git repository URL",
            ".zip archive URL",
            ".tar.gz archive URL",
            ".tgz archive URL",
        ],
        "endpoints": [
            "/scan",
            "/summary",
            "/report",
            "/download/excel",
            "/download/pdf",
        ],
    }


@app.post("/scan")
def scan_project(request: ScanRequest):
    temp_dir = None

    try:
        scan_target, temp_dir, source_type = prepare_scan_target(
            request.project_path
        )

        report_info = analyze_project(scan_target)

        return {
            "status": "success",
            "input": request.project_path,
            "source_type": source_type,
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

@app.post("/upload-scan")
async def upload_scan(file: UploadFile = File(...)):
    temp_dir = tempfile.mkdtemp(prefix="oss_upload_scan_")

    try:
        filename = file.filename.lower()

        if not (
            filename.endswith(".zip")
            or filename.endswith(".tar.gz")
            or filename.endswith(".tgz")
        ):
            raise HTTPException(
                status_code=400,
                detail="Only .zip, .tar.gz, and .tgz archives are supported.",
            )

        upload_path = Path(temp_dir) / file.filename

        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        extract_dir = Path(temp_dir) / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        if filename.endswith(".zip"):
            with zipfile.ZipFile(upload_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

        else:
            with tarfile.open(upload_path, "r:gz") as tar_ref:
                tar_ref.extractall(extract_dir)

        report_info = analyze_project(str(extract_dir))

        return {
            "status": "success",
            "source_type": "uploaded_archive",
            "summary": report_info["summary"],
            "results": report_info["results"],
            "json_report": report_info["json_report"],
            "csv_report": report_info["csv_report"],
            "excel_report": report_info.get("excel_report"),
            "pdf_report": report_info.get("pdf_report"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
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
@app.get("/download/sbom/cyclonedx")
def download_cyclonedx_sbom():
    if not CYCLONEDX_SBOM_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="CycloneDX SBOM not found.",
        )

    return FileResponse(
        path=CYCLONEDX_SBOM_PATH,
        filename="sbom_cyclonedx.json",
        media_type="application/json",
    )


@app.get("/download/sbom/spdx")
def download_spdx_sbom():
    if not SPDX_SBOM_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="SPDX SBOM not found.",
        )

    return FileResponse(
        path=SPDX_SBOM_PATH,
        filename="sbom_spdx.json",
        media_type="application/json",
    )