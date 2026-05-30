import re


def normalize_package_name(package_name: str) -> str:
    if not package_name:
        return "unknown"

    name = str(package_name).strip()

    # Remove environment markers
    name = name.split(";")[0].strip()

    # Remove Poetry/PEP508 bracketed version format:
    # "requests (>=2.0,<3.0)" -> "requests"
    name = re.sub(r"\s*\(.*?\)\s*$", "", name).strip()

    # Remove extras:
    # "celery[redis]" -> "celery"
    name = re.sub(r"\[.*?\]", "", name).strip()

    # Remove version operators:
    # "requests>=2.0" -> "requests"
    name = re.split(r"\s*(==|>=|<=|~=|>|<|!=|\^|~|\*)\s*", name)[0].strip()

    # Remove accidental quotes
    name = name.strip("\"'")

    # Normalize underscores for registry lookup friendliness
    name = name.replace("_", "-")

    return name.lower()


def normalize_version(version: str) -> str:
    if not version:
        return "unknown"

    value = str(version).strip()
    value = value.strip("\"'")

    # Remove environment markers
    value = value.split(";")[0].strip()

    # Remove wrapping parentheses
    value = value.strip("()").strip()

    if not value:
        return "unknown"

    return value


def normalize_dependency(dep: dict) -> dict:
    package = normalize_package_name(dep.get("package", "unknown"))
    version = normalize_version(dep.get("version", "unknown"))

    return {
        **dep,
        "package": package,
        "version": version,
    }


def deduplicate_dependencies(dependencies):
    unique = {}

    for dep in dependencies:
        normalized = normalize_dependency(dep)
        key = (
            normalized["package"],
            normalized.get("ecosystem", "unknown"),
        )

        if key == "unknown":
            continue

        # Prefer entries with known versions over unknown versions
        if key not in unique:
            unique[key] = normalized
        elif unique[key].get("version") == "unknown" and normalized.get("version") != "unknown":
            unique[key] = normalized

    return list(unique.values())
