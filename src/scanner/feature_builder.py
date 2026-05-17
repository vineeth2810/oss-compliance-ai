def map_license_family(license_name: str):
    license_name = license_name.lower()

    if any(x in license_name for x in ["mit", "apache", "bsd", "cc0", "unlicense"]):
        return "Permissive"

    if any(x in license_name for x in ["lgpl", "mpl", "epl", "cddl"]):
        return "Weak Copyleft"

    if any(x in license_name for x in ["gpl", "agpl"]):
        return "Strong Copyleft"

    if "proprietary" in license_name:
        return "Restricted"

    return "Unknown"


def build_scenario(
    package_name,
    version,
    license_name,
    project_type="commercial SaaS platform",
    distribution_model="hosted",
    usage="library"
):
    license_family = map_license_family(license_name)

    return {
        "package": package_name,
        "version": version,
        "license": license_name,
        "license_family": license_family,
        "project_type": project_type,
        "distribution_model": distribution_model,
        "usage": usage,
        "scenario": (
            f"License: {license_name} "
            f"License Family: {license_family} "
            f"Project Type: {project_type} "
            f"Distribution Model: {distribution_model} "
            f"Usage: {usage}"
        )
    }
