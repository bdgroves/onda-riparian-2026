"""ONDA riparian remote-sensing analysis package.

A 2026 rebuild of a 2018 volunteer GIS project tracking vegetation and
moisture change in eastern Oregon drainages using Landsat, Sentinel-2, and
Sentinel-1 imagery.

Submodules are imported lazily so that pure-python code (trends,
restoration) doesn't drag in earthengine-api.
"""

__version__ = "0.1.0"
__all__ = ["composites", "indices", "restoration", "sites", "trends", "viz"]


def __getattr__(name: str):
    if name in __all__:
        import importlib
        return importlib.import_module(f"onda.{name}")
    raise AttributeError(f"module 'onda' has no attribute {name!r}")
