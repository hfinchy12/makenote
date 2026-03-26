from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("makenote")
except PackageNotFoundError:
    __version__ = "unknown"
