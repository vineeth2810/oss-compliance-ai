import csv
import json
from pathlib import Path


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

    json_path = output_path / "compliance_report.json"
    csv_path = output_path / "compliance_report.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(structured_results, f, indent=2)

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
        "results": structured_results,
    }
