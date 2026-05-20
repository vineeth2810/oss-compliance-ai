import json

from src.scanner.dependency_normalizer import (
    normalize_package_name,
    normalize_version,
    deduplicate_dependencies,
)


def parse_package_lock(package_lock_path):
    dependencies = []

    with open(package_lock_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # npm lockfile v2/v3 format
    packages = data.get("packages", {})

    for path, package_data in packages.items():
        if not path.startswith("node_modules/"):
            continue

        package_name = path.replace("node_modules/", "", 1)

        version = package_data.get("version", "unknown")

        dependencies.append({
            "package": normalize_package_name(package_name),
            "version": normalize_version(version),
        })

    # npm lockfile v1 fallback
    legacy_dependencies = data.get("dependencies", {})

    for package_name, package_data in legacy_dependencies.items():
        version = package_data.get("version", "unknown")

        dependencies.append({
            "package": normalize_package_name(package_name),
            "version": normalize_version(version),
        })

    return deduplicate_dependencies(dependencies)
