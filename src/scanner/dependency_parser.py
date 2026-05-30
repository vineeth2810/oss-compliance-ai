from pathlib import Path
import re


def clean_requirement_line(line: str):
    line = line.strip()

    if not line:
        return None

    if line.startswith("#"):
        return None

    # Skip pip options and flags
    ignored_prefixes = (
        "--index-url",
        "--extra-index-url",
        "--trusted-host",
        "--find-links",
        "--no-build-isolation",
        "--use-pep517",
        "--pre",
        "-f",
        "-e",
    )

    if line.startswith(ignored_prefixes):
        return None

    # Remove inline comments
    if "#" in line:
        line = line.split("#", 1)[0].strip()

    # Remove environment markers
    if ";" in line:
        line = line.split(";", 1)[0].strip()

    # Remove extras: build[uv] -> build
    if "[" in line and "]" in line:
        import re
        line = re.sub(r"\[.*?\]", "", line).strip()

    if not line:
        return None

    return line

def parse_dependency_line(line: str):
    operators = [
        "==",
        ">=",
        "<=",
        "~=",
        "!=",
        ">",
        "<",
    ]

    for operator in operators:
        if operator in line:
            name, version = line.split(operator, 1)

            return {
                "package": name.strip(),
                "version": f"{operator}{version.strip()}",
            }

    return {
        "package": line.strip(),
        "version": "unknown",
    }

def detect_scope_from_path(path):
    path_str = str(path).lower()

    if "test" in path_str:
        return "test"

    if "doc" in path_str:
        return "docs"

    if "dev" in path_str:
        return "dev"

    if "build" in path_str:
        return "build"

    if "benchmark" in path_str:
        return "benchmark"

    return "runtime"

def load_requirements_recursive(
    requirements_path,
    visited=None,
):
    if visited is None:
        visited = set()

    requirements_path = Path(requirements_path).resolve()

    if requirements_path in visited:
        return []

    visited.add(requirements_path)

    dependencies = []

    if not requirements_path.exists():
        return dependencies

    with open(
        requirements_path,
        "r",
        encoding="utf-8",
    ) as file:

        for raw_line in file:
            line = clean_requirement_line(raw_line)

            if not line:
                continue

            # Handle nested requirements
            if (
                line.startswith("-r ")
                or line.startswith("--requirement ")
            ):
                parts = line.split()

                if len(parts) >= 2:
                    nested_file = (
                        requirements_path.parent / parts[1]
                    )

                    dependencies.extend(
                        load_requirements_recursive(
                            nested_file,
                            visited,
                        )
                    )

                continue

            dependency = parse_dependency_line(line)

            dependency["scope"] = detect_scope_from_path(
                requirements_path
            )

            dependencies.append(dependency)

    return dependencies


def parse_requirements(file_path: str):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    dependencies = load_requirements_recursive(path)

    return dependencies