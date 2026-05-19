import json
import random
from pathlib import Path


LICENSE_SCENARIOS = [
    {
        "license": "MIT",
        "family": "Permissive",
        "base_risk": "Low",
    },
    {
        "license": "BSD-3-Clause",
        "family": "Permissive",
        "base_risk": "Low",
    },
    {
        "license": "Apache-2.0",
        "family": "Permissive",
        "base_risk": "Low",
    },
    {
        "license": "LGPL-3.0-only",
        "family": "Weak Copyleft",
        "base_risk": "Medium",
    },
    {
        "license": "MPL-2.0",
        "family": "Weak Copyleft",
        "base_risk": "Medium",
    },
    {
        "license": "GPL-3.0-only",
        "family": "Strong Copyleft",
        "base_risk": "High",
    },
    {
        "license": "AGPL-3.0-only",
        "family": "Network Copyleft",
        "base_risk": "High",
    },
]


PROJECT_TYPES = [
    "commercial SaaS platform",
    "distributed desktop application",
    "internal enterprise tool",
    "mobile application",
    "embedded device firmware",
]


DISTRIBUTION_MODELS = [
    "hosted",
    "redistributed",
    "internal-only",
]


LINKING_TYPES = [
    "dynamic",
    "static",
    "plugin",
    "service boundary",
]


USAGE_TYPES = [
    "runtime library",
    "build tool",
    "dev dependency",
    "optional plugin",
]


NETWORK_EXPOSURE = [
    "yes",
    "no",
]


MODIFICATION_STATUS = [
    "modified",
    "unmodified",
]


COMMERCIAL_USE = [
    "yes",
    "no",
]


def determine_contextual_risk(
    license_name,
    project_type,
    distribution_model,
    linking_type,
    usage_type,
    network_exposed,
    modified,
):
    lower = license_name.lower()

    if "agpl" in lower:
        if network_exposed == "yes":
            return (
                "High",
                "AGPL software exposed over a network may require source code disclosure obligations."
            )

        return (
            "Medium",
            "AGPL software is present but not network exposed."
        )

    if "gpl" in lower and "lgpl" not in lower:
        if distribution_model == "redistributed":
            return (
                "High",
                "GPL software redistributed within a product may impose strong copyleft obligations."
            )

        if usage_type == "build tool":
            return (
                "Medium",
                "GPL software used only as a build tool may reduce compliance exposure."
            )

        return (
            "High",
            "GPL licensed runtime dependency creates strong copyleft compliance obligations."
        )

    if "lgpl" in lower:
        if linking_type == "static":
            return (
                "High",
                "Static linking with LGPL software may trigger stronger redistribution obligations."
            )

        return (
            "Medium",
            "Dynamically linked LGPL software usually permits proprietary usage but requires compliance review."
        )

    if "mpl" in lower:
        if modified == "modified":
            return (
                "Medium",
                "Modified MPL files may require source disclosure of modified files."
            )

        return (
            "Low",
            "Unmodified MPL usage generally has manageable obligations."
        )

    if "apache" in lower:
        return (
            "Low",
            "Apache-2.0 is permissive but requires preservation of notices and patent terms."
        )

    return (
        "Low",
        "Permissive licenses generally create minimal compliance obligations."
    )


def build_prompt(
    package_name,
    version,
    license_name,
    license_family,
    project_type,
    distribution_model,
    linking_type,
    usage_type,
    network_exposed,
    modified,
    commercial_use,
):
    return f"""
Package: {package_name}
Version: {version}
License: {license_name}
License Family: {license_family}
Project Type: {project_type}
Distribution Model: {distribution_model}
Linking Type: {linking_type}
Usage Type: {usage_type}
Network Exposed: {network_exposed}
Modified: {modified}
Commercial Use: {commercial_use}

Analyze OSS compliance risk.
""".strip()


def build_response(risk, reason):
    return f"""
Risk: {risk}

Reason:
{reason}
""".strip()


def generate_dataset(num_samples=5000):
    rows = []

    for i in range(num_samples):
        license_info = random.choice(LICENSE_SCENARIOS)

        project_type = random.choice(PROJECT_TYPES)
        distribution_model = random.choice(DISTRIBUTION_MODELS)
        linking_type = random.choice(LINKING_TYPES)
        usage_type = random.choice(USAGE_TYPES)
        network_exposed = random.choice(NETWORK_EXPOSURE)
        modified = random.choice(MODIFICATION_STATUS)
        commercial_use = random.choice(COMMERCIAL_USE)

        package_name = f"package-{i}"
        version = f"{random.randint(1,10)}.{random.randint(0,9)}.{random.randint(0,9)}"

        risk, reason = determine_contextual_risk(
            license_info["license"],
            project_type,
            distribution_model,
            linking_type,
            usage_type,
            network_exposed,
            modified,
        )

        prompt = build_prompt(
            package_name,
            version,
            license_info["license"],
            license_info["family"],
            project_type,
            distribution_model,
            linking_type,
            usage_type,
            network_exposed,
            modified,
            commercial_use,
        )

        response = build_response(risk, reason)

        rows.append({
            "prompt": prompt,
            "response": response,
        })

    return rows


def save_jsonl(rows, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    dataset = generate_dataset(num_samples=5000)

    output_file = output_dir / "advanced_oss_dataset.jsonl"

    save_jsonl(dataset, output_file)

    print(f"Generated dataset: {output_file}")
    print(f"Total samples: {len(dataset)}")
