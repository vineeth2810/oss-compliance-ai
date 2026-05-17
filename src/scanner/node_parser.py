import json
from pathlib import Path


def parse_package_json(file_path: str):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    dependencies = []

    deps = data.get("dependencies", {})

    for package_name, version in deps.items():
        dependencies.append({
            "package": package_name,
            "version": version.replace("^", "").replace("~", "")
        })

    return dependencies
