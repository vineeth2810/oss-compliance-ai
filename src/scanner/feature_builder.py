def build_compliance_context(license_family: str):
    if license_family == "Permissive":
        return {
            "attribution_notice": "preserved",
            "license_text": "included",
            "source_modified": "no",
            "redistribution": "no",
            "network_exposed": "no",
            "license_confidence": "high"
        }

    if license_family == "Weak Copyleft":
        return {
            "attribution_notice": "preserved",
            "license_text": "included",
            "source_modified": "possible",
            "redistribution": "possible",
            "network_exposed": "possible",
            "license_confidence": "medium"
        }

    if license_family in ["Strong Copyleft", "Network Copyleft"]:
        return {
            "attribution_notice": "preserved",
            "license_text": "included",
            "source_modified": "possible",
            "redistribution": "yes",
            "network_exposed": "yes",
            "license_confidence": "high"
        }

    if license_family in ["Unknown", "Restricted"]:
        return {
            "attribution_notice": "unknown",
            "license_text": "unknown",
            "source_modified": "unknown",
            "redistribution": "unknown",
            "network_exposed": "unknown",
            "license_confidence": "low"
        }

    return {
        "attribution_notice": "unknown",
        "license_text": "unknown",
        "source_modified": "unknown",
        "redistribution": "unknown",
        "network_exposed": "unknown",
        "license_confidence": "low"
    }


def build_scenario(
    package_name,
    version,
    license_name,
    license_family,
    ecosystem,
    package_manager,
    project_type="commercial SaaS platform",
    distribution_model="hosted",
    usage="library",
    dependency_scope="runtime",
    direct_or_transitive="direct",
    is_dev_dependency="no",
    linking_type="dynamic",
    commercial_use="yes",
):
    compliance_context = build_compliance_context(license_family)

    scenario = (
        f"Package: {package_name} "
        f"Version: {version} "
        f"Ecosystem: {ecosystem} "
        f"Package Manager: {package_manager} "
        f"License: {license_name} "
        f"License Family: {license_family} "
        f"Dependency Scope: {dependency_scope} "
        f"Direct or Transitive: {direct_or_transitive} "
        f"Development Dependency: {is_dev_dependency} "
        f"Project Type: {project_type} "
        f"Distribution Model: {distribution_model} "
        f"Usage: {usage} "
        f"Linking Type: {linking_type} "
        f"Network Exposed: {compliance_context['network_exposed']} "
        f"Commercial Use: {commercial_use} "
        f"Attribution Notice: {compliance_context['attribution_notice']} "
        f"License Text: {compliance_context['license_text']} "
        f"Source Modified: {compliance_context['source_modified']} "
        f"Redistribution: {compliance_context['redistribution']} "
        f"License Confidence: {compliance_context['license_confidence']} "
        f"Dependency scope is {dependency_scope}. "
    )

    return {
        "package": package_name,
        "version": version,
        "ecosystem": ecosystem,
        "package_manager": package_manager,
        "license": license_name,
        "license_family": license_family,
        "dependency_scope": dependency_scope,
        "direct_or_transitive": direct_or_transitive,
        "is_dev_dependency": is_dev_dependency,
        "project_type": project_type,
        "distribution_model": distribution_model,
        "usage": usage,
        "linking_type": linking_type,
        "network_exposed": compliance_context["network_exposed"],
        "commercial_use": commercial_use,
        "attribution_notice": compliance_context["attribution_notice"],
        "license_text": compliance_context["license_text"],
        "source_modified": compliance_context["source_modified"],
        "redistribution": compliance_context["redistribution"],
        "license_confidence": compliance_context["license_confidence"],
        "scenario": scenario

    }