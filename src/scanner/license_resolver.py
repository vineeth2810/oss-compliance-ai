from src.scanner.dynamic_license_resolver import resolve_dynamic_license

from src.scanner.spdx_normalizer import (
    classify_license_family
)


FALLBACK_LICENSE_MAP = {
    "gpl-lib": "GPL-3.0-only",
    "agpl-service": "AGPL-3.0-only",
    "unknown-package": "Unknown",
    "lgpl-media": "LGPL-2.1-only",
    "mpl-plugin": "MPL-2.0",
    "gpl-widget": "GPL-3.0-only",
    "lgpl-ui": "LGPL-3.0-only",
    "unknown-js-lib": "Unknown",
}


def resolve_license(package_name, ecosystem="unknown"):
    dynamic_license = resolve_dynamic_license(
        package_name=package_name,
        ecosystem=ecosystem
    )

    if dynamic_license != "Unknown":
        return dynamic_license

    return FALLBACK_LICENSE_MAP.get(
        package_name.lower(),
        "Unknown"
    )


def resolve_license_family(license_name):
    return classify_license_family(license_name)