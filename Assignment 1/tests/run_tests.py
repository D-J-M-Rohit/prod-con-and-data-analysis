"""
Test Runner
"""

from __future__ import annotations

import os
import sys
import time
import unittest
from typing import Optional

# Ensure "src" and "tests" are on the path when run from project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests(
    start_dir: Optional[str] = None,
    pattern: Optional[str] = None,
    verbosity: Optional[int] = None,
) -> bool:
    """
    Discover and run tests in the tests directory.

    Args:
        start_dir: Directory to start discovery from (defaults to this file's dir).
        pattern: Glob pattern for test files.
                 Defaults to 'test_shared_buffer.py' (unit tests only).
                 To include integration tests as well, set TESTS_PATTERN to 'test_*.py'.
    Returns:
        True if all tests passed, False otherwise.
    """
    start_dir = (
        start_dir
        or os.environ.get("TESTS_START_DIR")
        or os.path.dirname(os.path.abspath(__file__))
    )

    # Default: only the unit tests file (as the prompt requested "unit tests").
    default_pattern = "test_shared_buffer.py"
    pattern = pattern or os.environ.get("TESTS_PATTERN") or default_pattern

    try:
        verbosity = int(os.environ.get("TESTS_VERBOSITY", "")) if verbosity is None else verbosity
    except ValueError:
        verbosity = 2
    if verbosity is None:
        verbosity = 2

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=start_dir, pattern=pattern)

    runner = unittest.TextTestRunner(verbosity=verbosity)

    t0 = time.perf_counter()
    try:
        result = runner.run(suite)
    except KeyboardInterrupt:
        print("\n\n Test run interrupted by user (KeyboardInterrupt).")
        return False
    elapsed = time.perf_counter() - t0

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Start directory: {start_dir}")
    print(f"Pattern:         {pattern}")
    print(f"Verbosity:       {verbosity}")
    print(f"Elapsed:         {elapsed:.2f}s")
    print("-" * 70)
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total - failures - errors
    print(f"Tests run:       {total}")
    print(f"Successes:       {successes}")
    print(f"Failures:        {failures}")
    print(f"Errors:          {errors}")

    if result.wasSuccessful():
        print("\n All tests passed!")
    else:
        print("\n Some tests failed!")

    print("=" * 70 + "\n")
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
