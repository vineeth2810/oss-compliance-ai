import re
import requests

from src.scanner.spdx_normalizer import normalize_license
from src.scanner.dependency_normalizer import normalize_package_name



def clean_package_name(package_name: str):
    return normalize_package_name(package_name)


def resolve_pypi_license(package_name):
    clean_name = clean_package_name(package_name)
    url = f"https://pypi.org/pypi/{clean_name}/json"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return "Unknown"

        data = response.json()
        info = data.get("info", {})

        # 1. PEP 639 license expression
        license_expression = info.get("license_expression")
        normalized = normalize_license(license_expression)

        if normalized != "Unknown":
            return normalized

        # 2. Direct license field
        license_value = info.get("license")
        normalized = normalize_license(license_value)

        if normalized != "Unknown":
            return normalized

        # 3. Classifiers
        classifiers = info.get("classifiers", [])

        for classifier in classifiers:
            if classifier.startswith("License ::"):
                normalized = normalize_license(classifier)

                if normalized != "Unknown":
                    return normalized

        # 4. Summary / description fallback, conservative
        summary = info.get("summary", "")
        normalized = normalize_license(summary)

        if normalized != "Unknown":
            return normalized

        return "Unknown"

    except Exception:
        return "Unknown"


def resolve_npm_license(package_name):
    clean_name = clean_package_name(package_name)
    url = f"https://registry.npmjs.org/{clean_name}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return "Unknown"

        data = response.json()

        license_value = data.get("license")
        normalized = normalize_license(license_value)

        if normalized != "Unknown":
            return normalized

        latest = data.get("dist-tags", {}).get("latest")

        if latest:
            latest_data = data.get("versions", {}).get(latest, {})

            license_value = latest_data.get("license")
            normalized = normalize_license(license_value)

            if normalized != "Unknown":
                return normalized

            licenses_value = latest_data.get("licenses")
            normalized = normalize_license(licenses_value)

            if normalized != "Unknown":
                return normalized

        return "Unknown"

    except Exception:
        return "Unknown"


def resolve_dynamic_license(package_name, ecosystem):
    if ecosystem == "python":
        return resolve_pypi_license(package_name)

    if ecosystem == "node":
        return resolve_npm_license(package_name)

    return "Unknown"