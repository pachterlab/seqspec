from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("seqspec")
except Exception:
    __version__ = "@+unknown"
