import tomllib

from src.scanner.dependency_normalizer import (
    normalize_package_name,
    normalize_version,
    deduplicate_dependencies,
)


def parse_dependency_string(dep_string):
    dep_string = str(dep_string).strip()

    if not dep_string:
        return None

    dep_string = dep_string.split(";")[0].strip()

    # PEP 508 style:
    # requests>=2.0
    # cachecontrol[filecache] (>=0.14,<0.15)
    if "(" in dep_string and ")" in dep_string:
        name_part = dep_string.split("(", 1)[0].strip()
        version_part = dep_string.split("(", 1)[1].split(")", 1)[0].strip()

        return {
            "package": normalize_package_name(name_part),
            "version": normalize_version(version_part),
        }

    for operator in ["==", ">=", "<=", "~=", "!=", ">", "<", "^", "~"]:
        if operator in dep_string:
            name_part, version_part = dep_string.split(operator, 1)

            return {
                "package": normalize_package_name(name_part),
                "version": normalize_version(operator + version_part),
            }

    return {
        "package": normalize_package_name(dep_string),
        "version": "unknown",
    }


def parse_poetry_dependency(package_name, version_value):
    if package_name.lower() == "python":
        return None

    if isinstance(version_value, str):
        version = version_value
    elif isinstance(version_value, dict):
        version = version_value.get("version", "unknown")
    else:
        version = "unknown"

    return {
        "package": normalize_package_name(package_name),
        "version": normalize_version(version),
    }


def parse_pyproject(pyproject_path):
    dependencies = []

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    # PEP 621:
    # [project]
    # dependencies = [...]
    project = data.get("project", {})
    project_dependencies = project.get("dependencies", [])

    for dep in project_dependencies:
        parsed = parse_dependency_string(dep)

        if parsed:
            dependencies.append(parsed)

    # PEP 621 optional dependencies:
    # [project.optional-dependencies]
    optional_dependencies = project.get("optional-dependencies", {})

    for group_deps in optional_dependencies.values():
        for dep in group_deps:
            parsed = parse_dependency_string(dep)

            if parsed:
                dependencies.append(parsed)

    # Poetry:
    # [tool.poetry.dependencies]
    poetry = data.get("tool", {}).get("poetry", {})
    poetry_dependencies = poetry.get("dependencies", {})

    for package_name, version_value in poetry_dependencies.items():
        parsed = parse_poetry_dependency(package_name, version_value)

        if parsed:
            dependencies.append(parsed)

    # Poetry old dev dependencies:
    # [tool.poetry.dev-dependencies]
    poetry_dev_dependencies = poetry.get("dev-dependencies", {})

    for package_name, version_value in poetry_dev_dependencies.items():
        parsed = parse_poetry_dependency(package_name, version_value)

        if parsed:
            dependencies.append(parsed)

    # Poetry groups:
    # [tool.poetry.group.dev.dependencies]
    poetry_groups = poetry.get("group", {})

    for group_data in poetry_groups.values():
        group_dependencies = group_data.get("dependencies", {})

        for package_name, version_value in group_dependencies.items():
            parsed = parse_poetry_dependency(package_name, version_value)

            if parsed:
                dependencies.append(parsed)

    return deduplicate_dependencies(dependencies)