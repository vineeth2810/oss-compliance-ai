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


def calculate_overall_project_risk(risk_counts):
    high_count = risk_counts.get("High", 0)
    medium_count = risk_counts.get("Medium", 0)
    unknown_count = risk_counts.get("Unknown", 0)

    if high_count > 0:
        return "High"

    if unknown_count > 0:
        return "High"

    if medium_count > 0:
        return "Medium"

    return "Low"


def generate_project_summary(structured_results):
    risks = [item["risk"] for item in structured_results]
    risk_counts = Counter(risks)

    top_risks = [
        item for item in structured_results
        if item["risk"] in ["High", "Unknown"]
    ]

    medium_risks = [
        item for item in structured_results
        if item["risk"] == "Medium"
    ]

    overall_project_risk = calculate_overall_project_risk(risk_counts)

    summary = {
        "total_dependencies": len(structured_results),
        "risk_summary": {
            "Low": risk_counts.get("Low", 0),
            "Medium": risk_counts.get("Medium", 0),
            "High": risk_counts.get("High", 0),
            "Unknown": risk_counts.get("Unknown", 0),
        },
        "overall_project_risk": overall_project_risk,
        "top_risky_packages": [
            {
                "package": item["package"],
                "version": item["version"],
                "license": item["license"],
                "license_family": item["license_family"],
                "risk": item["risk"],
                "reason": item["reason"],
            }
            for item in top_risks[:10]
        ],
        "medium_risk_packages": [
            {
                "package": item["package"],
                "version": item["version"],
                "license": item["license"],
                "license_family": item["license_family"],
                "risk": item["risk"],
                "reason": item["reason"],
            }
            for item in medium_risks[:10]
        ],
    }

    return summary


def generate_reports(results, output_dir="outputs"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    structured_results = []

    for item in results:
        risk, reason = extract_risk_and_reason(item["prediction"])

        structured_results.append({
            "package": item["package"],
            "version": item["version"],
            "license": item["license"],
            "license_family": item["license_family"],
            "risk": risk,
            "reason": reason,
        })

    project_summary = generate_project_summary(structured_results)

    json_path = output_path / "compliance_report.json"
    csv_path = output_path / "compliance_report.csv"
    summary_path = output_path / "project_summary.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(structured_results, f, indent=2)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(project_summary, f, indent=2)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "package",
                "version",
                "license",
                "license_family",
                "risk",
                "reason",
            ],
        )

        writer.writeheader()
        writer.writerows(structured_results)

    return {
        "json_report": str(json_path),
        "csv_report": str(csv_path),
        "summary_report": str(summary_path),
        "results": structured_results,
        "summary": project_summary,
    }