import json
import re
from pathlib import Path


def parse_cmake(project_path):
    dependencies = []

    cmake_files = list(
        Path(project_path).rglob("CMakeLists.txt")
    )

    for file_path in cmake_files:
        try:
            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            find_packages = re.findall(
                r"find_package\(([^ )]+)",
                content,
            )

            target_libs = re.findall(
                r"target_link_libraries\([^)]+?\s([A-Za-z0-9_\-]+)",
                content,
            )

            for package in set(find_packages + target_libs):
                dependencies.append({
                    "package": package,
                    "version": "unknown",
                    "ecosystem": "cpp",
                    "package_manager": "cmake",
                })

        except Exception:
            continue

    return dependencies


def parse_vcpkg(project_path):
    dependencies = []

    vcpkg_files = list(
        Path(project_path).rglob("vcpkg.json")
    )

    for file_path in vcpkg_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for dep in data.get("dependencies", []):
                if isinstance(dep, str):
                    dependencies.append({
                        "package": dep,
                        "version": "unknown",
                        "ecosystem": "cpp",
                        "package_manager": "vcpkg",
                    })

                elif isinstance(dep, dict):
                    dependencies.append({
                        "package": dep.get("name"),
                        "version": dep.get("version>=", "unknown"),
                        "ecosystem": "cpp",
                        "package_manager": "vcpkg",
                    })

        except Exception:
            continue

    return dependencies


def parse_conan(project_path):
    dependencies = []

    conan_files = list(
        Path(project_path).rglob("conanfile.txt")
    )

    for file_path in conan_files:
        try:
            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            in_requires = False

            for line in content.splitlines():
                line = line.strip()

                if line.lower() == "[requires]":
                    in_requires = True
                    continue

                if line.startswith("[") and line.endswith("]"):
                    in_requires = False

                if in_requires and line:
                    package = line.split("/")[0]
                    version = (
                        line.split("/")[1]
                        if "/" in line
                        else "unknown"
                    )

                    dependencies.append({
                        "package": package,
                        "version": version,
                        "ecosystem": "cpp",
                        "package_manager": "conan",
                    })

        except Exception:
            continue

    return dependencies


def parse_cpp_dependencies(project_path):
    dependencies = []

    dependencies.extend(parse_cmake(project_path))
    dependencies.extend(parse_vcpkg(project_path))
    dependencies.extend(parse_conan(project_path))

    unique = {}

    for dep in dependencies:
        key = (
            dep["package"],
            dep["ecosystem"],
        )

        unique[key] = dep

    return list(unique.values())
