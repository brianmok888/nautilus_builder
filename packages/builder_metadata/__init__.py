"""Builder metadata — canonical version and build info."""
from packages.builder_metadata.version import get_canonical_version
from packages.builder_metadata.build_info import get_build_info

__all__ = ["get_canonical_version", "get_build_info"]
