import os
import sys


def get_env(key: str, default: str = "") -> str:
    """Retrieve an environment variable with an optional default."""
    return os.getenv(key, default)


def is_windows() -> bool:
    """Return True if the current platform is Windows."""
    return sys.platform.startswith("win")


def resource_path(relative_path: str) -> str:
    """Return absolute path to a resource, compatible with PyInstaller bundles."""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)
