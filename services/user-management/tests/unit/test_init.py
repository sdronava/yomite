"""
Unit tests for src/__init__.py module.

Tests module initialization and version string.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_version_string_exists():
    """Test that __version__ can be imported and is a string."""
    # Import the __init__ module
    import __init__ as src_init

    assert hasattr(src_init, "__version__")
    assert isinstance(src_init.__version__, str)
    assert len(src_init.__version__) > 0


def test_version_format():
    """Test that __version__ follows semantic versioning format."""
    import __init__ as src_init

    # Should be in format X.Y.Z
    parts = src_init.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_module_docstring_exists():
    """Test that module has proper documentation."""
    import __init__ as src_init

    assert src_init.__doc__ is not None
    assert len(src_init.__doc__) > 0
