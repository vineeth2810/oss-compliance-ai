import csv
import json
from pathlib import Path
from collections import Counter


def extract_risk_and_reason(prediction: str):
    risk = "Unknown"
    reason = "No reason provided."

    for line in prediction.splitlines():
        line = line.strip()

        if line.lower().startswith("risk:"):
            risk = line.split(":", 1)[1].strip()

        elif line.lower().startswith("reason:"):
            reason = line.split(":", 1)[1].strip()

    return risk, reason


def build_package_url(package_name, ecosystem):
    clean_name = package_name.split("[")[0]

    if ecosystem == "python":
        return f"https://pypi.org/project/{clean_name}/"

    if ecosystem == "node":
        return f"https://www.npmjs.com/package/{clean_name}"

    return ""


def calculate_overall_project_risk(risk_counts):
    if risk_counts.get("High", 0) > 0:
        return "High"

    if risk_counts.get("Unknown", 0) > 0:
        return "High"

    if risk_counts.get("Medium", 0) > 0:
        return "Medium"

    return "Low"


def generate_project_summary(structured_results):
    risks = [item["risk"] for item in structured_results]
    risk_counts = Counter(risks)

    high_risks = [item for item in structured_results if item["risk"] == "High"]
    medium_risks = [item for item in structured_results if item["risk"] == "Medium"]
    low_risks = [item for item in structured_results if item["risk"] == "Low"]

    return {
        "total_dependencies": len(structured_results),
        "risk_summary": {
            "Low": risk_counts.get("Low", 0),
            "Medium": risk_counts.get("Medium", 0),
            "High": risk_counts.get("High", 0),
            "Unknown": risk_counts.get("Unknown", 0),
        },
        "overall_project_risk": calculate_overall_project_risk(risk_counts),
        "top_risky_packages": high_risks[:10],
        "medium_risk_packages": medium_risks[:10],
        "low_risk_packages": low_risks[:10],
    }


def generate_reports(results, output_dir="outputs"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    structured_results = []

    for item in results:
        risk, reason = extract_risk_and_reason(item["prediction"])

        ecosystem = item.get("ecosystem", "unknown")
        package_name = item["package"]

        structured_results.append({
            "package": package_name,
            "version": item["version"],
            "ecosystem": ecosystem,
            "package_manager": item.get("package_manager", "unknown"),
            "license": item["license"],
            "license_family": item["license_family"],
            "risk": risk,
            "reason": reason,
            "package_url": build_package_url(package_name, ecosystem),
        })

    project_summary = generate_project_summary(structured_results)

    json_path = output_path / "compliance_report.json"
    csv_path = output_path / "compliance_report.csv"
    summary_path = output_path / "project_summary.json"
    excel_path = output_path / "compliance_report.xlsx"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(structured_results, f, indent=2)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(project_summary, f, indent=2)

    fieldnames = [
        "package",
        "version",
        "ecosystem",
        "package_manager",
        "license",
        "license_family",
        "risk",
        "reason",
        "package_url",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(structured_results)

    try:
        import pandas as pd

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            pd.DataFrame(structured_results).to_excel(
                writer,
                index=False,
                sheet_name="Dependency Report",
            )

            pd.DataFrame([project_summary["risk_summary"]]).to_excel(
                writer,
                index=False,
                sheet_name="Risk Summary",
            )

            pd.DataFrame(project_summary["top_risky_packages"]).to_excel(
                writer,
                index=False,
                sheet_name="High Risk",
            )

            pd.DataFrame(project_summary["medium_risk_packages"]).to_excel(
                writer,
                index=False,
                sheet_name="Medium Risk",
            )

    except Exception:
        pass

    return {
        "json_report": str(json_path),
        "csv_report": str(csv_path),
        "summary_report": str(summary_path),
        "excel_report": str(excel_path),
        "results": structured_results,
        "summary": project_summary,
    }