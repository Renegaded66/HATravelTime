"""Load integration modules without importing Home Assistant.

The integration package needs Home Assistant to import, but ``const.py``,
``location.py`` and ``api.py`` are deliberately free of Home Assistant imports.
This helper builds a throw-away package so their relative imports work.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "traveltimefree"
PACKAGE_NAME = "_traveltime_under_test"


def _ensure_package() -> None:
    if PACKAGE_NAME in sys.modules:
        return
    package = types.ModuleType(PACKAGE_NAME)
    package.__path__ = [str(PACKAGE_DIR)]  # type: ignore[attr-defined]
    sys.modules[PACKAGE_NAME] = package


def load(module: str):
    """Import ``custom_components/traveltimefree/<module>.py`` as part of a fake package."""
    _ensure_package()
    full_name = f"{PACKAGE_NAME}.{module}"
    if full_name in sys.modules:
        return sys.modules[full_name]

    spec = importlib.util.spec_from_file_location(full_name, PACKAGE_DIR / f"{module}.py")
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = loaded
    spec.loader.exec_module(loaded)
    return loaded
