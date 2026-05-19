import tomllib


def parse_dependency_string(dep_string):
    dep_string = dep_string.strip()

    if not dep_string:
        return None

    clean_name = dep_string

    for operator in ["==", ">=", "<=", "~=", ">", "<"]:
        if operator in dep_string:
            clean_name = dep_string.split(operator)[0].strip()
            version = dep_string.split(operator)[1].strip()
            return {
                "package": clean_name,
                "version": version
            }

    return {
        "package": clean_name,
        "version": "unknown"
    }


def parse_pyproject(pyproject_path):
    dependencies = []

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    # PEP 621 format:
    # [project]
    # dependencies = [...]
    project = data.get("project", {})
    project_dependencies = project.get("dependencies", [])

    for dep in project_dependencies:
        parsed = parse_dependency_string(dep)

        if parsed:
            dependencies.append(parsed)

    # Optional dependencies:
    # [project.optional-dependencies]
    optional_dependencies = project.get("optional-dependencies", {})

    for group_deps in optional_dependencies.values():
        for dep in group_deps:
            parsed = parse_dependency_string(dep)

            if parsed:
                dependencies.append(parsed)

    # Poetry format:
    # [tool.poetry.dependencies]
    poetry = data.get("tool", {}).get("poetry", {})
    poetry_dependencies = poetry.get("dependencies", {})

    for package_name, version_value in poetry_dependencies.items():
        if package_name.lower() == "python":
            continue

        if isinstance(version_value, str):
            version = version_value
        elif isinstance(version_value, dict):
            version = version_value.get("version", "unknown")
        else:
            version = "unknown"

        dependencies.append({
            "package": package_name,
            "version": version
        })

    # Poetry dev dependencies:
    # [tool.poetry.group.dev.dependencies]
    poetry_groups = poetry.get("group", {})

    for group_data in poetry_groups.values():
        group_dependencies = group_data.get("dependencies", {})

        for package_name, version_value in group_dependencies.items():
            if isinstance(version_value, str):
                version = version_value
            elif isinstance(version_value, dict):
                version = version_value.get("version", "unknown")
            else:
                version = "unknown"

            dependencies.append({
                "package": package_name,
                "version": version
            })

    # Remove duplicates
    unique = {}

    for dep in dependencies:
        key = dep["package"].lower()
        unique[key] = dep

    return list(unique.values())
