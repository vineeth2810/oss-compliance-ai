from src.reporting.report_generator import generate_reports

from src.scanner.scanner_pipeline import (
    scan_python_project,
    scan_node_project
)

from src.inference.qwen_inference import predict_risk


def analyze_python_project(requirements_path):
    scenarios = scan_python_project(requirements_path)

    results = []

    for item in scenarios:
        print(f"Analyzing: {item['package']}")

        prediction = predict_risk(item["scenario"])

        result = {
            "package": item["package"],
            "version": item["version"],
            "license": item["license"],
            "license_family": item["license_family"],
            "prediction": prediction
        }

        results.append(result)

    return results


def analyze_node_project(package_json_path):
    scenarios = scan_node_project(package_json_path)

    results = []

    for item in scenarios:
        print(f"Analyzing: {item['package']}")

        prediction = predict_risk(item["scenario"])

        result = {
            "package": item["package"],
            "version": item["version"],
            "license": item["license"],
            "license_family": item["license_family"],
            "prediction": prediction
        }

        results.append(result)

    return results


if __name__ == "__main__":

    print("=" * 60)
    print("PYTHON PROJECT ANALYSIS")
    print("=" * 60)

    python_results = analyze_python_project(
        "examples/sample_python_project/requirements.txt"
    )

    for item in python_results:
        print(item)

    print("\n" + "=" * 60)
    print("NODE PROJECT ANALYSIS")
    print("=" * 60)

    node_results = analyze_node_project(
        "examples/sample_node_project/package.json"
    )

    for item in node_results:
        print(item)

    all_results = python_results + node_results

    report_info = generate_reports(all_results)

    print("\n" + "=" * 60)
    print("REPORT GENERATED")
    print("=" * 60)
    print("JSON:", report_info["json_report"])
    print("CSV:", report_info["csv_report"])