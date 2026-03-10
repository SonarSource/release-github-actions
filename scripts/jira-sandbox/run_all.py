#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Orchestrator: runs setup → verify → cleanup in sequence.
Cleanup always runs, even if verify fails.

Exit code: 0 if all steps pass, 1 otherwise.
"""

import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_script(name: str) -> int:
    """Runs a script and returns its exit code."""
    script = os.path.join(SCRIPT_DIR, f"{name}.py")
    print(f"\n{'=' * 60}")
    print(f"Running: {name}.py")
    print("=" * 60)
    result = subprocess.run([sys.executable, script], cwd=SCRIPT_DIR)
    return result.returncode


def main():
    setup_rc = run_script("setup")
    if setup_rc != 0:
        print(f"\n❌ setup.py failed (exit code {setup_rc}). Attempting cleanup anyway.")

    verify_rc = run_script("verify")
    cleanup_rc = run_script("cleanup")

    print(f"\n{'=' * 60}")
    print("OVERALL RESULT")
    print("=" * 60)
    print(f"  setup.py:   {'✅ passed' if setup_rc == 0 else '❌ failed'}")
    print(f"  verify.py:  {'✅ passed' if verify_rc == 0 else '❌ failed'}")
    print(f"  cleanup.py: {'✅ passed' if cleanup_rc == 0 else '❌ failed'}")

    if setup_rc == 0 and verify_rc == 0 and cleanup_rc == 0:
        print("\n✅ All steps passed.")
        sys.exit(0)
    else:
        print("\n❌ One or more steps failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
