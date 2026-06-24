import os
import sys


def safe_path(path, base=None):
    """Resolve path and ensure it stays within base (cwd by default). Exits 1 if it escapes.

    Only relative paths are subject to the boundary check — absolute paths are returned
    as-is after normalisation. This prevents path-traversal attacks (S8707) on relative
    CLI arguments (e.g. ../../etc/passwd) while allowing callers to pass arbitrary
    absolute paths such as /tmp or $RUNNER_TEMP state files.
    """
    resolved = os.path.realpath(path)
    if not os.path.isabs(path):
        base_dir = os.path.realpath(base or os.getcwd())
        if resolved != base_dir and not resolved.startswith(base_dir + os.sep):
            print(f'ERROR: path {path!r} is outside the allowed directory', file=sys.stderr)
            sys.exit(1)
    return resolved
