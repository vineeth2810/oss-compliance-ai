from src.inference.qwen_inference import generate_response


def generate_ai_remediation(item):
    vulnerabilities = item.get("vulnerabilities", [])

    vulnerability_summary = "\n".join(
        [
            f"- {v.get('id')}: {v.get('summary')}"
            for v in vulnerabilities[:5]
        ]
    )

    if not vulnerability_summary:
        vulnerability_summary = "No known vulnerabilities found."

    prompt = f"""
You are an OSS compliance and security remediation assistant.

Analyze the following dependency and provide practical remediation guidance.

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

Known Vulnerabilities:
{vulnerability_summary}

Provide:
1. Priority level
2. Why this matters
3. Recommended actions
4. Safer alternative or upgrade guidance
5. Final engineering recommendation

Keep the answer concise and practical.
"""

    return generate_response(prompt)
