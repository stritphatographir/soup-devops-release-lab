import pytest
from read_back import public_files_ready


def test_unverified_platform_wheel_is_not_accepted():
    entries = [
        {"filename": "tested.whl"}, {"filename": "tested.tar.gz"},
        {"filename": "untested_windows.whl"},
    ]
    with pytest.raises(ValueError, match="unexpected"):
        public_files_ready(entries, {"tested.whl", "tested.tar.gz"})


def test_partial_index_can_be_retried_but_exact_index_is_required():
    expected = {"tested.whl", "tested.tar.gz"}
    assert not public_files_ready([{"filename": "tested.whl"}], expected)
    assert public_files_ready([{"filename": name} for name in expected], expected)


def test_duplicate_index_entries_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        public_files_ready([{"filename": "tested.whl"}] * 2, {"tested.whl"})
