from src.scanner.dependency_parser import parse_requirements
from src.scanner.node_parser import parse_package_json
from src.scanner.pyproject_parser import parse_pyproject

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


def build_results(dependencies, ecosystem, package_manager):
    results = []

    for dep in dependencies:
        package_name = dep["package"]
        version = dep["version"]

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
    print("NODE PROJECT")
    print("=" * 60)

    node_results = scan_node_project(
        "examples/sample_node_project/package.json"
    )

    for item in node_results:
        print(item)