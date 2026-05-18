import requests

from src.scanner.spdx_normalizer import normalize_license


def resolve_pypi_license(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return "Unknown"

        data = response.json()
        info = data.get("info", {})

        license_value = info.get("license")
        normalized = normalize_license(license_value)

        if normalized != "Unknown":
            return normalized

        license_expression = info.get("license_expression")
        normalized = normalize_license(license_expression)

        if normalized != "Unknown":
            return normalized

        classifiers = info.get("classifiers", [])

        for classifier in classifiers:
            if "License ::" in classifier:
                normalized = normalize_license(classifier)

                if normalized != "Unknown":
                    return normalized

        project_urls = info.get("project_urls") or {}

        for key, value in project_urls.items():
            combined = f"{key} {value}"
            normalized = normalize_license(combined)

            if normalized != "Unknown":
                return normalized

        return "Unknown"

    except Exception:
        return "Unknown"


def resolve_npm_license(package_name):
    url = f"https://registry.npmjs.org/{package_name}"

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