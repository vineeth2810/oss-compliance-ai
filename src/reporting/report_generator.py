import csv
import json

from pathlib import Path
from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from src.security.osv_client import (
    lookup_vulnerabilities,
    calculate_security_risk,
    build_vulnerability_url,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

from src.reporting.sbom_generator import (
    generate_cyclonedx_sbom,
    generate_spdx_sbom,
)

from src.security.osv_client import (
    lookup_vulnerabilities,
    calculate_security_risk,
)


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
RISK_PRIORITY = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Unknown": 4,
}


def calculate_combined_risk(
    license_risk,
    security_risk,
):
    if RISK_PRIORITY.get(security_risk, 0) > RISK_PRIORITY.get(license_risk, 0):
        return security_risk

    return license_risk


def build_combined_reason(
    license_risk,
    security_risk,
):
    if (
        license_risk == "High"
        and security_risk == "High"
    ):
        return (
            "High license compliance risk combined with "
            "multiple known security vulnerabilities."
        )

    if security_risk == "High":
        return (
            "Package contains multiple known vulnerabilities "
            "that increase production security risk."
        )

    if license_risk == "High":
        return (
            "Package introduces strong copyleft or network "
            "license obligations."
        )

    if (
        license_risk == "Medium"
        or security_risk == "Medium"
    ):
        return (
            "Package has moderate compliance or security considerations."
        )

    return "Low combined compliance and security risk."


def generate_risk_chart(risk_summary, chart_path):
    labels = []
    values = []

    for key, value in risk_summary.items():
        if value > 0:
            labels.append(key)
            values.append(value)

    if not values:
        labels = ["No Data"]
        values = [1]

    plt.figure(figsize=(5, 5))
    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.title("Risk Distribution")

    plt.savefig(chart_path, bbox_inches="tight")
    plt.close()


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


def build_pdf_report(summary, structured_results, pdf_path, chart_path):
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "OSS Compliance AI Report",
            styles["Title"],
        )
    )

    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph(
            f"Overall Project Risk: <b>{summary['overall_project_risk']}</b>",
            styles["Heading2"],
        )
    )

    elements.append(
        Paragraph(
            f"Total Dependencies: {summary['total_dependencies']}",
            styles["BodyText"],
        )
    )

    elements.append(Spacer(1, 12))

    risk_table_data = [
        ["Risk Level", "Count"],
    ]

    for key, value in summary["risk_summary"].items():
        risk_table_data.append([key, str(value)])

    risk_table = Table(risk_table_data)

    risk_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    )

    elements.append(risk_table)

    elements.append(Spacer(1, 18))

    if Path(chart_path).exists():
        chart = Image(str(chart_path), width=300, height=300)
        elements.append(chart)

    elements.append(Spacer(1, 24))

    high_risks = summary["top_risky_packages"]

    if high_risks:
        elements.append(
            Paragraph(
                "Top High Risk Packages",
                styles["Heading2"],
            )
        )

        table_data = [
            ["Package", "License", "Risk"],
        ]

        for item in high_risks:
            table_data.append([
                item["package"],
                item["license"],
                item["risk"],
            ])

        high_table = Table(table_data)

        high_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ])
        )

        elements.append(high_table)

    elements.append(Spacer(1, 18))

    elements.append(
        Paragraph(
            "Generated by OSS Compliance AI",
            styles["Italic"],
        )
    )

    doc.build(elements)


def generate_reports(results, output_dir="outputs"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    structured_results = []

    for item in results:
        risk, reason = extract_risk_and_reason(item["prediction"])

        ecosystem = item.get("ecosystem", "unknown")

        package_name = item["package"]
        version = item["version"]

        vulnerabilities = lookup_vulnerabilities(
            package_name=package_name,
            version=version,
            ecosystem=ecosystem,
        )

        security_risk = calculate_security_risk(vulnerabilities)

        structured_results.append({
            "package": package_name,
            "version": version,
            "ecosystem": ecosystem,
            "package_manager": item.get("package_manager", "unknown"),
            "license": item["license"],
            "license_family": item["license_family"],

            # License risk
            "risk": risk,
            "reason": reason,

            # Security risk
            "security_risk": security_risk,
            "vulnerability_count": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,

            # Combined risk
            "combined_risk": calculate_combined_risk(
                risk,
                security_risk,
            ),

            "combined_reason": build_combined_reason(
                risk,
                security_risk,
            ),

            # Package URL
            "package_url": build_package_url(
                package_name,
                ecosystem,
            ),
        })

    summary = generate_project_summary(structured_results)

    json_path = output_path / "compliance_report.json"
    csv_path = output_path / "compliance_report.csv"
    summary_path = output_path / "project_summary.json"
    excel_path = output_path / "compliance_report.xlsx"
    pdf_path = output_path / "compliance_report.pdf"
    chart_path = output_path / "risk_chart.png"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(structured_results, f, indent=2)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    fieldnames = [
        "package",
        "version",
        "ecosystem",
        "package_manager",
        "license",
        "license_family",
        "risk",
        "security_risk",
        "vulnerability_count",
        "vulnerability_url",
        "combined_risk",
        "combined_reason",
        "reason",
        "package_url",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        csv_results = []

        for item in structured_results:
            csv_item = item.copy()

            # Remove nested vulnerability objects for CSV export
            csv_item.pop("vulnerabilities", None)

            csv_results.append(csv_item)

        writer.writerows(csv_results)

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        pd.DataFrame(csv_results).to_excel(
            writer,
            index=False,
            sheet_name="Dependency Report",
        )

        pd.DataFrame([summary["risk_summary"]]).to_excel(
            writer,
            index=False,
            sheet_name="Risk Summary",
        )

    generate_risk_chart(
        summary["risk_summary"],
        chart_path,
    )

    build_pdf_report(
        summary,
        structured_results,
        pdf_path,
        chart_path,
    )

    cyclonedx_sbom = generate_cyclonedx_sbom(structured_results)
    spdx_sbom = generate_spdx_sbom(structured_results)

    return {
        "json_report": str(json_path),
        "csv_report": str(csv_path),
        "summary_report": str(summary_path),
        "excel_report": str(excel_path),
        "pdf_report": str(pdf_path),
        "results": structured_results,
        "cyclonedx_sbom": cyclonedx_sbom,
        "spdx_sbom": spdx_sbom,
        "summary": summary,
    }