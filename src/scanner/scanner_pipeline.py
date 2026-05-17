from src.scanner.dependency_parser import parse_requirements
from src.scanner.license_resolver import resolve_license
from src.scanner.feature_builder import build_scenario


def scan_requirements_project(requirements_path: str):
    dependencies = parse_requirements(requirements_path)

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
    results = scan_requirements_project(
        "examples/sample_python_project/requirements.txt"
    )

    for item in results:
        print(item)
