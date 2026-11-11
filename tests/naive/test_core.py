"""These tests deliberately never launch the CLI or inspect a built wheel."""

import pytest

from soup_release_lab.core import validate_name, validate_workers


def test_valid_library_call():
    assert validate_name(" service ") == "service"
    assert validate_workers(3) == 3


def test_invalid_worker_count():
    with pytest.raises(ValueError, match="between"):
        validate_workers(0)
