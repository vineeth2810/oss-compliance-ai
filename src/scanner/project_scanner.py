import sys
from pathlib import Path

from src.scanner.scanner_pipeline import (
    scan_python_project,
    scan_pyproject,
    scan_node_project,
)

from src.inference.qwen_inference import predict_risk
from src.reporting.report_generator import generate_reports


SUPPORTED_FILES = {
    "requirements.txt": "python_requirements",
    "pyproject.toml": "python_pyproject",
    "package.json": "node",
}


def find_dependency_files(project_path):
    project_root = Path(project_path)

    if not project_root.exists():
        raise FileNotFoundError(f"Project path not found: {project_path}")

    discovered_files = []

    ignored_dirs = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        "dist",
        "build",
    }

    for file_path in project_root.rglob("*"):
        if any(part in ignored_dirs for part in file_path.parts):
            continue

        if file_path.name in SUPPORTED_FILES:
            discovered_files.append({
                "path": str(file_path),
                "ecosystem": SUPPORTED_FILES[file_path.name],
            })

    return discovered_files


def analyze_discovered_file(file_info):
    ecosystem = file_info["ecosystem"]
    path = file_info["path"]

    if ecosystem == "python_requirements":
        return scan_python_project(path)

    if ecosystem == "python_pyproject":
        return scan_pyproject(path)

    if ecosystem == "node":
        return scan_node_project(path)

    return []


def analyze_project(project_path):
    dependency_files = find_dependency_files(project_path)

    print("Discovered dependency files:")

    for item in dependency_files:
        print(f"- {item['ecosystem']}: {item['path']}")

    all_scenarios = []

    for file_info in dependency_files:
        scenarios = analyze_discovered_file(file_info)
        all_scenarios.extend(scenarios)

    results = []

    for item in all_scenarios:
        print(f"Analyzing: {item['package']}")

        prediction = predict_risk(item["scenario"])

        results.append({
            "package": item["package"],
            "version": item["version"],
            "ecosystem": item.get("ecosystem", "unknown"),
            "package_manager": item.get("package_manager", "unknown"),
            "license": item["license"],
            "license_family": item["license_family"],
            "prediction": prediction,
        })

    report_info = generate_reports(results)

    print("\nReport generated:")
    print("JSON:", report_info["json_report"])
    print("CSV:", report_info["csv_report"])
    print("SUMMARY:", report_info["summary_report"])
    print("EXCEL:", report_info["excel_report"])
    print("PDF:", report_info["pdf_report"])
    print("OVERALL RISK:", report_info["summary"]["overall_project_risk"])

    return report_info


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print("python -m src.scanner.project_scanner <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]

    analyze_project(project_path)