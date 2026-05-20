import json
from pathlib import Path


OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_cyclonedx_sbom(results):
    components = []

    for item in results:
        component = {
            "type": "library",
            "name": item["package"],
            "version": item["version"],
            "licenses": [
                {
                    "license": {
                        "id": item["license"]
                    }
                }
            ],
            "properties": [
                {
                    "name": "risk",
                    "value": item["risk"],
                },
                {
                    "name": "license_family",
                    "value": item["license_family"],
                },
            ],
        }

        if item.get("package_url"):
            component["purl"] = item["package_url"]

        components.append(component)

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "tool": {
                "vendor": "OSS Compliance AI",
                "name": "OSS Compliance AI Scanner",
            }
        },
        "components": components,
    }

    output_path = OUTPUT_DIR / "sbom_cyclonedx.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2)

    return str(output_path)


def generate_spdx_sbom(results):
    packages = []

    for item in results:
        package = {
            "SPDXID": f"SPDXRef-{item['package']}",
            "name": item["package"],
            "versionInfo": item["version"],
            "licenseConcluded": item["license"],
            "licenseDeclared": item["license"],
            "downloadLocation": item.get("package_url", "NOASSERTION"),
        }

        packages.append(package)

    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "OSS Compliance AI SBOM",
        "documentNamespace": "https://oss-compliance-ai.local/spdx",
        "packages": packages,
    }

    output_path = OUTPUT_DIR / "sbom_spdx.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2)

    return str(output_path)
