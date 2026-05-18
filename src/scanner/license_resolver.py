LICENSE_MAP = {
    "numpy": "BSD-3-Clause",
    "pandas": "BSD-3-Clause",
    "requests": "Apache-2.0",
    "flask": "BSD-3-Clause",
    "django": "BSD-3-Clause",
    "scikit-learn": "BSD-3-Clause",
    "tensorflow": "Apache-2.0",
    "torch": "BSD-3-Clause",
    "gpl-lib": "GPL-3.0",
    "agpl-service": "AGPL-3.0",
    "unknown-package": "Unknown",
    "lgpl-media": "LGPL-2.1",
    "mpl-plugin": "MPL-2.0",
    "lgpl-ui": "LGPL-3.0",
    "gpl-widget": "GPL-3.0",
    "unknown-js-lib": "Unknown",

    "express": "MIT",
    "react": "MIT",
    "axios": "MIT",
    "lodash": "MIT"

}

def resolve_license(package_name: str):
    return LICENSE_MAP.get(package_name.lower(), "Unknown")
