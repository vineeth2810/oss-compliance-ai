from src.scanner.dependency_parser import parse_requirements
from src.scanner.node_parser import parse_package_json

from src.scanner.license_resolver import resolve_license
from src.scanner.feature_builder import build_scenario


def scan_python_project(requirements_path: str):
    dependencies = parse_requirements(requirements_path)

    return build_results(dependencies)


def scan_node_project(package_json_path: str):
    dependencies = parse_package_json(package_json_path)

    return build_results(dependencies)


def build_results(dependencies):
    results = []

    for dep in dependencies:
        package_name = dep["package"]
        version = dep["version"]

        license_name = resolve_license(package_name)

        scenario = build_scenario(
            package_name=package_name,
            version=version,
            license_name=license_name
        )

        results.append(scenario)

    return results


if __name__ == "__main__":

    print("=" * 60)
    print("PYTHON PROJECT")
    print("=" * 60)

    python_results = scan_python_project(
        "examples/sample_python_project/requirements.txt"
    )

    for item in python_results:
        print(item)

    print("\n" + "=" * 60)
    print("NODE PROJECT")
    print("=" * 60)

    node_results = scan_node_project(
        "examples/sample_node_project/package.json"
    )

    for item in node_results:
        print(item)