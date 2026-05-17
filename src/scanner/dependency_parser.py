from pathlib import Path


def parse_requirements(file_path: str):
    dependencies = []

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "==" in line:
                name, version = line.split("==", 1)
            else:
                name, version = line, "unknown"

            dependencies.append({
                "package": name.strip(),
                "version": version.strip()
            })

    return dependencies
