import json
import re
from pathlib import Path

from src.scanner.license_resolver import (
    resolve_license,
    resolve_license_family,
)

from src.scanner.feature_builder import build_scenario


KNOWN_CPP_LICENSES = {
    "openssl": "Apache-2.0",
    "zlib": "Zlib",
    "boost": "BSL-1.0",
    "qt": "LGPL-3.0-only",
    "glibc": "LGPL-2.1-only",
    "musl": "MIT",
    "libpng": "Libpng",
    "sqlite": "Public-Domain",
    "curl": "curl",
    "libcurl": "curl",
    "protobuf": "BSD-3-Clause",
    "absl": "Apache-2.0",
    "abseil": "Apache-2.0",
    "abseil-cpp": "Apache-2.0",
    "gtest": "BSD-3-Clause",
    "googletest": "BSD-3-Clause",
    "threads": "Unknown",
    "protobuf": "BSD-3-Clause",
    "absl": "Apache-2.0",
    "abseil": "Apache-2.0",
    "abseil-cpp": "Apache-2.0",
    "gtest": "BSD-3-Clause",
    "googletest": "BSD-3-Clause",
    "benchmark": "Apache-2.0",
    "re2": "BSD-3-Clause",
    "upb": "BSD-3-Clause",
    "utf8_range": "MIT",
}


def normalize_cpp_package_name(name):
    if not name:
        return "unknown"

    return str(name).strip().lower()


def parse_cmake(project_path):
    dependencies = []

    for file_path in Path(project_path).rglob("CMakeLists.txt"):
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        packages = re.findall(
            r"find_package\s*\(\s*([A-Za-z0-9_\-]+)",
            content,
            flags=re.IGNORECASE,
        )

        for package in packages:
            dependencies.append({
                "package": normalize_cpp_package_name(package),
                "version": "unknown",
                "ecosystem": "cpp",
                "package_manager": "cmake",
            })

    return dependencies


def parse_vcpkg(project_path):
    dependencies = []

    for file_path in Path(project_path).rglob("vcpkg.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for dep in data.get("dependencies", []):
            if isinstance(dep, str):
                package = dep
                version = "unknown"
            elif isinstance(dep, dict):
                package = dep.get("name", "unknown")
                version = dep.get("version>=", "unknown")
            else:
                continue

            dependencies.append({
                "package": normalize_cpp_package_name(package),
                "version": version,
                "ecosystem": "cpp",
                "package_manager": "vcpkg",
            })

    return dependencies


def parse_conan(project_path):
    dependencies = []

    for file_path in Path(project_path).rglob("conanfile.txt"):
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        in_requires = False

        for line in content.splitlines():
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if line.lower() == "[requires]":
                in_requires = True
                continue

            if line.startswith("[") and line.endswith("]"):
                in_requires = False
                continue

            if in_requires:
                if "/" in line:
                    package, version = line.split("/", 1)
                else:
                    package = line
                    version = "unknown"

                dependencies.append({
                    "package": normalize_cpp_package_name(package),
                    "version": version,
                    "ecosystem": "cpp",
                    "package_manager": "conan",
                })

    return dependencies


def parse_cpp_dependencies(project_path):
    dependencies = []

    dependencies.extend(parse_cmake(project_path))
    dependencies.extend(parse_vcpkg(project_path))
    dependencies.extend(parse_conan(project_path))

    unique = {}

    for dep in dependencies:
        key = dep["package"]
        unique[key] = dep

    return list(unique.values())


def resolve_cpp_license(package_name):
    clean_name = normalize_cpp_package_name(package_name)

    if clean_name in KNOWN_CPP_LICENSES:
        return KNOWN_CPP_LICENSES[clean_name]

    return resolve_license(
        package_name=clean_name,
        ecosystem="cpp",
    )


def scan_cpp_project(project_path):
    dependencies = parse_cpp_dependencies(project_path)

    results = []

    for dep in dependencies:
        package_name = dep["package"]
        version = dep["version"]

        license_name = resolve_cpp_license(package_name)
        license_family = resolve_license_family(license_name)

        scenario = build_scenario(
            package_name=package_name,
            version=version,
            license_name=license_name,
            license_family=license_family,
            ecosystem="cpp",
            package_manager=dep.get("package_manager", "unknown"),
        )

        results.append(scenario)

    return results
