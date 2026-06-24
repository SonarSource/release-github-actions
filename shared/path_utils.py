import os
import sys


def safe_path(path, base=None):
    """Resolve path and ensure it stays within base (cwd by default). Exits 1 if it escapes."""
    base_dir = os.path.realpath(base or os.getcwd())
    resolved = os.path.realpath(path)
    if resolved != base_dir and not resolved.startswith(base_dir + os.sep):
        print(f'ERROR: path {path!r} is outside the allowed directory', file=sys.stderr)
        sys.exit(1)
    return resolved
