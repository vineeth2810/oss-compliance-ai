from pathlib import Path

from src.scanner.scanner_pipeline import (
    scan_python_project,
    scan_node_project
)

from src.inference.qwen_inference import predict_risk
from src.reporting.report_generator import generate_reports


SUPPORTED_FILES = {
    "requirements.txt": "python",
    "package.json": "node"
}


def find_dependency_files(project_path):
    project_root = Path(project_path)

    if not project_root.exists():
        raise FileNotFoundError(f"Project path not found: {project_path}")

    discovered_files = []

    for file_path in project_root.rglob("*"):
        if file_path.name in SUPPORTED_FILES:
            discovered_files.append({
                "path": str(file_path),
                "ecosystem": SUPPORTED_FILES[file_path.name]
            })

    return discovered_files


def analyze_discovered_file(file_info):
    ecosystem = file_info["ecosystem"]
    path = file_info["path"]

    if ecosystem == "python":
        return scan_python_project(path)

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
    print("SUMMARY:", report_info["summary_report"])
    print("OVERALL RISK:", report_info["summary"]["overall_project_risk"])
    

    return report_info


import sys


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print("python -m src.scanner.project_scanner <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]

    analyze_project(project_path)
