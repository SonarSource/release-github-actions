import os
import sys


def safe_path(path, base=None):
    resolved = os.path.realpath(path)
    base_dir = os.path.realpath(base) if base else os.path.dirname(resolved)
    if resolved != base_dir and not resolved.startswith(base_dir + os.sep):
        print(f'ERROR: path {path!r} is outside the allowed directory', file=sys.stderr)
        sys.exit(1)
    return resolved
