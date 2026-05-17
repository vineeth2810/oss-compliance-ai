LICENSE_MAP = {
    "numpy": "BSD-3-Clause",
    "pandas": "BSD-3-Clause",
    "requests": "Apache-2.0",
    "flask": "BSD-3-Clause",
    "django": "BSD-3-Clause",
    "scikit-learn": "BSD-3-Clause",
    "tensorflow": "Apache-2.0",
    "torch": "BSD-3-Clause"
}


def resolve_license(package_name: str):
    return LICENSE_MAP.get(package_name.lower(), "Unknown")
