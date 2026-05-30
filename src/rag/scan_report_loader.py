import json
from pathlib import Path
from collections import Counter


def load_latest_scan_reports(output_dir="outputs"):
    documents = []

    report_path = Path(output_dir) / "compliance_report.json"
    summary_path = Path(output_dir) / "project_summary.json"
    cyclonedx_path = Path(output_dir) / "sbom_cyclonedx.json"
    spdx_path = Path(output_dir) / "sbom_spdx.json"

    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        documents.append({
            "source": str(report_path),
            "content": build_computed_scan_insights(report),
        })

        text_parts = ["# Latest Dependency Compliance Report"]

        for item in report:
            text_parts.append(
                f"""
Package: {item.get("package")}
Version: {item.get("version")}
Ecosystem: {item.get("ecosystem")}
License: {item.get("license")}
License Family: {item.get("license_family")}
License Risk: {item.get("risk")}
Security Risk: {item.get("security_risk")}
Combined Risk: {item.get("combined_risk")}
Vulnerability Count: {item.get("vulnerability_count")}
Reason: {item.get("reason")}
Combined Reason: {item.get("combined_reason")}
AI Remediation: {item.get("ai_remediation")}
"""
            )

        documents.append({
            "source": str(report_path),
            "content": "\n".join(text_parts),
        })

    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

        documents.append({
            "source": str(summary_path),
            "content": "# Latest Project Summary\n" + json.dumps(summary, indent=2),
        })

    if cyclonedx_path.exists():
        with open(cyclonedx_path, "r", encoding="utf-8") as f:
            cyclonedx = json.load(f)

        documents.append({
            "source": str(cyclonedx_path),
            "content": "# Latest CycloneDX SBOM\n" + json.dumps(cyclonedx, indent=2),
        })

    if spdx_path.exists():
        with open(spdx_path, "r", encoding="utf-8") as f:
            spdx = json.load(f)

        documents.append({
            "source": str(spdx_path),
            "content": "# Latest SPDX SBOM\n" + json.dumps(spdx, indent=2),
        })

    return documents


def build_computed_scan_insights(report):
    total_packages = len(report)

    license_counter = Counter(item.get("license", "Unknown") for item in report)
    family_counter = Counter(item.get("license_family", "Unknown") for item in report)
    license_risk_counter = Counter(item.get("risk", "Unknown") for item in report)
    security_risk_counter = Counter(item.get("security_risk", "Low") for item in report)
    combined_risk_counter = Counter(item.get("combined_risk", "Low") for item in report)

    gpl_packages = [
        item for item in report
        if "GPL" in str(item.get("license", "")).upper()
    ]

    agpl_packages = [
        item for item in report
        if "AGPL" in str(item.get("license", "")).upper()
    ]

    lgpl_packages = [
        item for item in report
        if "LGPL" in str(item.get("license", "")).upper()
    ]

    vulnerable_packages = [
        item for item in report
        if int(item.get("vulnerability_count", 0) or 0) > 0
    ]

    high_combined_risk_packages = [
        item for item in report
        if item.get("combined_risk") == "High"
    ]

    package_names = sorted(
        set(
            item.get("package")
            for item in report
            if item.get("package")
        )
    )

    lines = [
        "# Computed Scan Insights",
        f"Total packages scanned: {total_packages}",
        "",
        "Latest scan package list:",
        "Packages in latest scan: " + ", ".join(package_names),
        "",
        "License counts:",
    ]

    for license_name, count in license_counter.items():
        lines.append(f"- {license_name}: {count}")

    lines.extend([
        "",
        "License family counts:",
    ])

    for family, count in family_counter.items():
        lines.append(f"- {family}: {count}")

    lines.extend([
        "",
        "License risk counts:",
    ])

    for risk, count in license_risk_counter.items():
        lines.append(f"- {risk}: {count}")

    lines.extend([
        "",
        "Security risk counts:",
    ])

    for risk, count in security_risk_counter.items():
        lines.append(f"- {risk}: {count}")

    lines.extend([
        "",
        "Combined risk counts:",
    ])

    for risk, count in combined_risk_counter.items():
        lines.append(f"- {risk}: {count}")

    lines.extend([
        "",
        f"GPL licensed packages found: {len(gpl_packages)}",
    ])

    for item in gpl_packages:
        lines.append(
            f"- {item.get('package')} "
            f"({item.get('license')}, "
            f"license risk {item.get('risk')}, "
            f"combined risk {item.get('combined_risk')})"
        )

    lines.extend([
        "",
        f"AGPL licensed packages found: {len(agpl_packages)}",
    ])

    for item in agpl_packages:
        lines.append(
            f"- {item.get('package')} "
            f"({item.get('license')}, "
            f"license risk {item.get('risk')}, "
            f"combined risk {item.get('combined_risk')})"
        )

    lines.extend([
        "",
        f"LGPL licensed packages found: {len(lgpl_packages)}",
    ])

    for item in lgpl_packages:
        lines.append(
            f"- {item.get('package')} "
            f"({item.get('license')}, "
            f"license risk {item.get('risk')}, "
            f"combined risk {item.get('combined_risk')})"
        )

    lines.extend([
        "",
        f"Packages with known vulnerabilities: {len(vulnerable_packages)}",
    ])

    for item in vulnerable_packages:
        lines.append(
            f"- {item.get('package')} "
            f"version {item.get('version')} "
            f"has {item.get('vulnerability_count')} vulnerabilities "
            f"and security risk {item.get('security_risk')}"
        )

    lines.extend([
        "",
        f"High combined risk packages: {len(high_combined_risk_packages)}",
    ])

    for item in high_combined_risk_packages:
        lines.append(
            f"- {item.get('package')} "
            f"license risk {item.get('risk')}, "
            f"security risk {item.get('security_risk')}, "
            f"combined risk {item.get('combined_risk')}"
        )

    if vulnerable_packages:
        sorted_vulnerable = sorted(
            vulnerable_packages,
            key=lambda item: int(item.get("vulnerability_count", 0) or 0),
            reverse=True,
        )

        top = sorted_vulnerable[0]

        lines.extend([
            "",
            "Recommended first fix:",
            (
                f"- Start with {top.get('package')} "
                f"version {top.get('version')} because it has "
                f"{top.get('vulnerability_count')} known vulnerabilities "
                f"and security risk {top.get('security_risk')}."
            ),
        ])

    lines.append("")
    lines.append("Recommended remediation priorities:")

    priority_items = sorted(
        report,
        key=lambda x: (
            x.get("combined_risk") != "High",
            x.get("combined_risk") != "Medium",
        )
    )

    for item in priority_items[:5]:
        lines.append(
            f"- {item.get('package')} "
            f"(combined risk: {item.get('combined_risk')}) "
            f"Reason: {item.get('combined_reason')}"
        )

        remediation = item.get("ai_remediation")

        if remediation:
            lines.append(f"AI Recommendation: {remediation}")
        high_security_packages = [
        item for item in report
        if item.get("security_risk") == "High"
    ]

    lines.append("")
    lines.append(f"High security risk packages found: {len(high_security_packages)}")

    for item in high_security_packages:
        lines.append(
            f"- {item.get('package')} "
            f"version {item.get('version')} "
            f"has security risk {item.get('security_risk')} "
            f"with {item.get('vulnerability_count')} vulnerabilities "
            f"and combined risk {item.get('combined_risk')}"
        )

    if high_security_packages:
        top_security_package = sorted(
            high_security_packages,
            key=lambda item: int(item.get("vulnerability_count", 0) or 0),
            reverse=True,
        )[0]

        lines.append("")
        lines.append(
            "Package with highest security risk: "
            f"{top_security_package.get('package')} "
            f"version {top_security_package.get('version')} "
            f"with {top_security_package.get('vulnerability_count')} vulnerabilities."
        )  
    if high_security_packages:
        most_vulnerable = sorted(
            high_security_packages,
            key=lambda item: int(
            item.get("vulnerability_count", 0) or 0
        ),
            reverse=True,
        )[0]

        lines.append("")
        lines.append(
            "Most vulnerable package in latest scan: "
            f"{most_vulnerable.get('package')} "
            f"with {most_vulnerable.get('vulnerability_count')} "
            f"known vulnerabilities."
        )          

    return "\n".join(lines)