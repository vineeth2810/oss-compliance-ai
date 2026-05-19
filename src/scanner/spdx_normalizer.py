import re
import requests


SPDX_URL = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"

SPDX_LICENSES = {}


def load_spdx_licenses():
    global SPDX_LICENSES

    if SPDX_LICENSES:
        return SPDX_LICENSES

    try:
        response = requests.get(SPDX_URL, timeout=20)

        if response.status_code != 200:
            print("Failed to fetch SPDX license list")
            return {}

        data = response.json()
        licenses = data.get("licenses", [])

        SPDX_LICENSES = {
            item["licenseId"].lower(): item["licenseId"]
            for item in licenses
        }

        return SPDX_LICENSES

    except Exception as e:
        print("SPDX fetch error:", e)
        return {}


def clean_license_text(raw_license):
    if raw_license is None:
        return ""

    if isinstance(raw_license, dict):
        raw_license = (
            raw_license.get("type")
            or raw_license.get("name")
            or raw_license.get("license")
            or ""
        )

    if isinstance(raw_license, list):
        raw_license = " OR ".join(str(item) for item in raw_license)

    text = str(raw_license).strip()
    text = text.replace("(", " ").replace(")", " ").replace(",", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def choose_primary_license(valid_tokens):
    priority_order = [
        "AGPL",
        "SSPL",
        "GPL",
        "LGPL",
        "MPL",
        "EPL",
        "CDDL",
        "Apache",
        "BSD",
        "MIT",
        "ISC",
        "Zlib",
        "CC0",
        "Unlicense",
    ]

    for priority in priority_order:
        for token in valid_tokens:
            if priority.lower() in token.lower():
                return token

    return valid_tokens[0] if valid_tokens else "Unknown"


def normalize_classifier(text):
    lower = text.lower()

    classifier_aliases = {
        "license :: osi approved :: mit license": "MIT",
        "license :: osi approved :: apache software license": "Apache-2.0",
        "license :: osi approved :: bsd license": "BSD-3-Clause",
        "license :: osi approved :: isc license": "ISC",
        "license :: osi approved :: zlib/libpng license": "Zlib",
        "license :: osi approved :: mozilla public license 2.0 mpl 2.0": "MPL-2.0",
        "license :: osi approved :: gnu general public license v3 gplv3": "GPL-3.0-only",
        "license :: osi approved :: gnu lesser general public license v3 lgplv3": "LGPL-3.0-only",
        "license :: osi approved :: gnu affero general public license v3": "AGPL-3.0-only",
    }

    if lower in classifier_aliases:
        return classifier_aliases[lower]

    if lower.startswith("license ::"):
        if "mit license" in lower:
            return "MIT"

        if "apache software license" in lower:
            return "Apache-2.0"

        if "bsd license" in lower:
            return "BSD-3-Clause"

        if "isc license" in lower:
            return "ISC"

        if "mozilla public license" in lower:
            return "MPL-2.0"

        if "lesser general public license" in lower:
            return "LGPL-3.0-only"

        if "affero general public license" in lower:
            return "AGPL-3.0-only"

        if "general public license" in lower:
            return "GPL-3.0-only"

    return "Unknown"


def normalize_license(raw_license):
    text = clean_license_text(raw_license)

    if not text:
        return "Unknown"

    lower = text.lower()

    if lower in ["unknown", "none", "n/a", "not specified"]:
        return "Unknown"

    classifier_result = normalize_classifier(text)

    if classifier_result != "Unknown":
        return classifier_result

    spdx_licenses = load_spdx_licenses()

    if lower in spdx_licenses:
        return spdx_licenses[lower]

    alias_map = {
        "mit license": "MIT",
        "apache license 2.0": "Apache-2.0",
        "apache software license": "Apache-2.0",
        "apache software license 2.0": "Apache-2.0",
        "apache 2.0": "Apache-2.0",
        "bsd license": "BSD-3-Clause",
        "bsd 3-clause": "BSD-3-Clause",
        "bsd-3-clause license": "BSD-3-Clause",
        "bsd 2-clause": "BSD-2-Clause",
        "bsd-2-clause license": "BSD-2-Clause",
        "gplv3": "GPL-3.0-only",
        "gpl v3": "GPL-3.0-only",
        "gplv2": "GPL-2.0-only",
        "gpl v2": "GPL-2.0-only",
        "lgpl": "LGPL-3.0-only",
        "agpl": "AGPL-3.0-only",
        "mozilla public license 2.0": "MPL-2.0",
        "eclipse public license 2.0": "EPL-2.0",
        "common development and distribution license": "CDDL-1.0",
    }

    if lower in alias_map:
        return alias_map[lower]

    expression_tokens = re.split(r"\s+(and|or|with)\s+", lower)

    valid_tokens = []

    for token in expression_tokens:
        token = token.strip()

        if token in ["and", "or", "with", ""]:
            continue

        if token in spdx_licenses:
            valid_tokens.append(spdx_licenses[token])

    if valid_tokens:
        return choose_primary_license(valid_tokens)

    if "apache-2.0" in lower or "apache license 2.0" in lower:
        return "Apache-2.0"

    if "bsd-3-clause" in lower or "bsd 3-clause" in lower:
        return "BSD-3-Clause"

    if "bsd-2-clause" in lower or "bsd 2-clause" in lower:
        return "BSD-2-Clause"

    if "lgpl-2.1" in lower:
        return "LGPL-2.1-only"

    if "lgpl-3.0" in lower:
        return "LGPL-3.0-only"

    if "agpl-3.0" in lower:
        return "AGPL-3.0-only"

    if "gpl-3.0" in lower:
        return "GPL-3.0-only"

    if "gpl-2.0" in lower:
        return "GPL-2.0-only"

    if "mpl-2.0" in lower:
        return "MPL-2.0"

    if "epl-2.0" in lower:
        return "EPL-2.0"

    if "cddl-1.0" in lower:
        return "CDDL-1.0"

    if lower in ["isc", "isc license"]:
        return "ISC"

    if lower in ["zlib", "zlib license"]:
        return "Zlib"

    if lower in ["unlicense", "the unlicense"]:
        return "Unlicense"

    if lower in ["cc0", "cc0-1.0", "creative commons zero v1.0 universal"]:
        return "CC0-1.0"

    if "proprietary" in lower:
        return "Proprietary"

    if "custom" in lower:
        return "Custom"

    if "see license" in lower or "license file" in lower:
        return "Unknown"

    return "Unknown"


def classify_license_family(license_name):
    if not license_name:
        return "Unknown"

    lower = license_name.lower()

    network_copyleft = ["agpl", "sspl"]
    weak_copyleft = ["lgpl", "mpl", "epl", "cddl"]
    strong_copyleft = ["gpl"]
    permissive = [
        "mit",
        "apache",
        "bsd",
        "isc",
        "zlib",
        "python",
        "psf",
        "unlicense",
        "cc0",
        "0bsd",
    ]
    restricted = [
        "bsl",
        "elastic",
        "commons-clause",
        "proprietary",
        "custom",
    ]

    for item in network_copyleft:
        if item in lower:
            return "Network Copyleft"

    for item in weak_copyleft:
        if item in lower:
            return "Weak Copyleft"

    for item in strong_copyleft:
        if item in lower:
            return "Strong Copyleft"

    for item in permissive:
        if item in lower:
            return "Permissive"

    for item in restricted:
        if item in lower:
            return "Restricted"

    return "Unknown"