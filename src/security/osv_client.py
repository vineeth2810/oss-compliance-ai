import requests


OSV_API_URL = "https://api.osv.dev/v1/query"


def map_ecosystem_to_osv(ecosystem: str):
    ecosystem = (ecosystem or "").lower()

    if ecosystem == "python":
        return "PyPI"

    if ecosystem == "node":
        return "npm"

    return None


def lookup_vulnerabilities(package_name: str, version: str, ecosystem: str):
    osv_ecosystem = map_ecosystem_to_osv(ecosystem)

    if not osv_ecosystem:
        return []

    if not version or version == "unknown":
        return []

    # OSV expects exact versions, not ranges like >=1.0,<2
    if any(symbol in version for symbol in [">", "<", "^", "~", "*", ","]):
        return []

    payload = {
        "package": {
            "name": package_name,
            "ecosystem": osv_ecosystem,
        },
        "version": version,
    }

    try:
        response = requests.post(OSV_API_URL, json=payload, timeout=15)

        if response.status_code != 200:
            return []

        data = response.json()
        vulns = data.get("vulns", [])

        return [
            {
                "id": vuln.get("id"),
                "summary": vuln.get("summary", ""),
                "details": vuln.get("details", ""),
                "modified": vuln.get("modified", ""),
                "published": vuln.get("published", ""),
            }
            for vuln in vulns
        ]

    except Exception:
        return []


def calculate_security_risk(vulnerabilities):
    count = len(vulnerabilities)

    if count >= 3:
        return "High"

    if count >= 1:
        return "Medium"

    return "Low"
def build_vulnerability_url(package_name: str, ecosystem: str):
    ecosystem = (ecosystem or "").lower()

    if ecosystem == "python":
        return f"https://osv.dev/list?q={package_name}"

    if ecosystem == "node":
        return f"https://osv.dev/list?q={package_name}"

    return "https://osv.dev/"