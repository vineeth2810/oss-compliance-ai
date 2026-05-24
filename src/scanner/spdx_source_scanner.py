import re
from collections import Counter
from pathlib import Path

from src.scanner.license_resolver import resolve_license_family
from src.scanner.feature_builder import build_scenario


SOURCE_EXTENSIONS = {
    ".c",
    ".h",
    ".cpp",
    ".cc",
    ".cxx",
    ".hpp",
    ".hh",
    ".hxx",
    ".s",
    ".S",
    ".rs",
    ".go",
    ".java",
    ".js",
    ".ts",
    ".py",
}

SPECIAL_SOURCE_FILES = {
    "Makefile",
    "Kconfig",
}

SPDX_PATTERN = re.compile(
    r"SPDX-License-Identifier:\s*([A-Za-z0-9\.\-\+ WITH/()]+)",
    re.IGNORECASE,
)


def should_scan_source_file(file_path: Path):
    if file_path.name in SPECIAL_SOURCE_FILES:
        return True

    return file_path.suffix in SOURCE_EXTENSIONS


def extract_spdx_from_file(file_path: Path):
    licenses = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(30):
                line = f.readline()

                if not line:
                    break

                match = SPDX_PATTERN.search(line)

                if match:
                    licenses.append(match.group(1).strip())

    except Exception:
        return []

    return licenses


def scan_spdx_source_licenses(project_path):
    project_root = Path(project_path)

    license_counter = Counter()

    ignored_dirs = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        "dist",
        "build",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }

    for file_path in project_root.rglob("*"):
        if any(part in ignored_dirs for part in file_path.parts):
            continue

        if not file_path.is_file():
            continue

        if not should_scan_source_file(file_path):
            continue

        licenses = extract_spdx_from_file(file_path)

        for license_id in licenses:
            license_counter[license_id] += 1

    results = []

    for license_id, count in license_counter.items():
        license_family = resolve_license_family(license_id)

        package_name = f"source-files-{license_id.lower()}"

        scenario = build_scenario(
            package_name=package_name,
            version=f"{count} files",
            license_name=license_id,
            license_family=license_family,
            ecosystem="source",
            package_manager="spdx-source",
        )

        results.append({
            "package": package_name,
            "version": f"{count} files",
            "ecosystem": "source",
            "package_manager": "spdx-source",
            "license": license_id,
            "license_family": license_family,
            "scenario": scenario["scenario"],
        })

    return results
