"""
Bug condition exploration test for test coverage improvement.

This test verifies that code coverage reaches 80% or higher.
When run on unfixed code, this test FAILS, confirming the coverage gap exists.
When run on fixed code (after adding tests for uncovered paths), this test PASSES.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
"""

import subprocess
import sys
from pathlib import Path


def test_coverage_reaches_80_percent():
    """
    Property 1: Bug Condition - All Code Paths Executed

    For any code path in the uncovered modules (monitoring.py, error_handler.py,
    dynamodb_client.py, __init__.py), the fixed test suite SHALL execute that code
    path and measure it as covered by pytest-cov.

    This test MUST FAIL on unfixed code (confirming the coverage gap exists).
    This test MUST PASS on fixed code (confirming the gap is fixed).

    Expected counterexamples on unfixed code:
    - monitoring.py: 50% coverage (68 lines missing)
    - error_handler.py: 56% coverage (26 lines missing)
    - dynamodb_client.py: 73% coverage (28 lines missing)
    - src/__init__.py: 0% coverage (1 line missing)
    """
    # Run pytest with coverage reporting
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit/",
            "-v",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=json",
        ],
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True,
    )

    # Parse coverage from JSON report
    import json

    json_file = Path(__file__).parent.parent.parent / "coverage.json"

    if json_file.exists():
        with open(json_file) as f:
            coverage_data = json.load(f)
            total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
    else:
        # Fallback: parse from terminal output
        for line in result.stdout.split("\n"):
            if "TOTAL" in line:
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        total_coverage = float(parts[-2].rstrip("%"))
                        break
                    except (ValueError, IndexError):
                        total_coverage = 0

    # Assert that coverage is 80% or higher
    assert total_coverage >= 80, (
        f"Coverage is {total_coverage}%, but must be 80% or higher. "
        f"Uncovered code paths exist in: monitoring.py (50%), error_handler.py (56%), "
        f"dynamodb_client.py (73%), src/__init__.py (0%)"
    )
