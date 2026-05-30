from src.scanner.dependency_parser import parse_requirements
from src.scanner.node_parser import parse_package_json
from src.scanner.pyproject_parser import parse_pyproject
from src.scanner.package_lock_parser import parse_package_lock

from src.scanner.license_resolver import (
    resolve_license,
    resolve_license_family,
)

from src.scanner.feature_builder import build_scenario


def scan_python_project(requirements_path: str):
    dependencies = parse_requirements(requirements_path)

    return build_results(
        dependencies=dependencies,
        ecosystem="python",
        package_manager="pip",
    )


def scan_pyproject(pyproject_path: str):
    dependencies = parse_pyproject(pyproject_path)

    return build_results(
        dependencies=dependencies,
        ecosystem="python",
        package_manager="pyproject",
    )


def scan_node_project(package_json_path: str):
    dependencies = parse_package_json(package_json_path)

    return build_results(
        dependencies=dependencies,
        ecosystem="node",
        package_manager="npm",
    )


def scan_package_lock(package_lock_path: str):
    dependencies = parse_package_lock(package_lock_path)

    return build_results(
        dependencies=dependencies,
        ecosystem="node",
        package_manager="npm-lock",
    )


def normalize_package_name(package_name: str):
    package_name = str(package_name or "").strip()

    # Remove inline comments accidentally kept by parsers
    if "#" in package_name:
        package_name = package_name.split("#", 1)[0].strip()

    # Remove environment markers accidentally kept by parsers
    if ";" in package_name:
        package_name = package_name.split(";", 1)[0].strip()

    return package_name


def normalize_version(version: str):
    version = str(version or "unknown").strip()

    if not version:
        return "unknown"

    return version


def is_valid_dependency(dep):
    package_name = normalize_package_name(dep.get("package", ""))

    if not package_name:
        return False

    invalid_prefixes = (
        "-r",
        "--requirement",
        "--index-url",
        "--extra-index-url",
        "--find-links",
        "--trusted-host",
        "-f",
        "-e",
        "git+",
    )

    if package_name.startswith(invalid_prefixes):
        return False

    invalid_suffixes = (
        ".txt",
        ".md",
        ".rst",
    )

    if package_name.lower().endswith(invalid_suffixes):
        return False

    return True


def build_results(dependencies, ecosystem, package_manager):
    results = []

    seen = set()

    for dep in dependencies:
        if not is_valid_dependency(dep):
            continue

        package_name = normalize_package_name(dep["package"])
        version = normalize_version(dep.get("version", "unknown"))

        key = (
            package_name.lower(),
            version,
            ecosystem,
            package_manager,
        )

        if key in seen:
            continue

        seen.add(key)

        license_name = resolve_license(
            package_name=package_name,
            ecosystem=ecosystem,
        )

        license_family = resolve_license_family(license_name)

        scenario = build_scenario(
            package_name=package_name,
            version=version,
            license_name=license_name,
            license_family=license_family,
            ecosystem=ecosystem,
            package_manager=package_manager,
            dependency_scope=dep.get("scope", "runtime"),
        )

        results.append(scenario)

    return results


if __name__ == "__main__":

    print("=" * 60)
    print("PYTHON REQUIREMENTS PROJECT")
    print("=" * 60)

    python_results = scan_python_project(
        "examples/sample_python_project/requirements.txt"
    )

    for item in python_results:
        print(item)

    print("\n" + "=" * 60)
    print("PYPROJECT PROJECT")
    print("=" * 60)

    try:
        pyproject_results = scan_pyproject(
            "examples/sample_python_project/pyproject.toml"
        )

        for item in pyproject_results:
            print(item)

    except FileNotFoundError:
        print("No sample pyproject.toml found.")

    print("\n" + "=" * 60)
    print("NODE PACKAGE.JSON PROJECT")
    print("=" * 60)

    node_results = scan_node_project(
        "examples/sample_node_project/package.json"
    )

    for item in node_results:
        print(item)

    print("\n" + "=" * 60)
    print("NODE PACKAGE-LOCK PROJECT")
    print("=" * 60)

    try:
        lock_results = scan_package_lock(
            "frontend/package-lock.json"
        )

        for item in lock_results:
            print(item)

    except FileNotFoundError:
        print("No frontend/package-lock.json found.")