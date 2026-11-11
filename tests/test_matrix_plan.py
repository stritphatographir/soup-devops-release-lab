import pytest
from matrix_plan import plan, validate_plan


def test_fixed_matrix_requires_every_supported_environment():
    matrix = plan("fixed")
    assert len(matrix["include"]) == 15
    matrix["include"].pop()
    with pytest.raises(ValueError, match="full support"):
        validate_plan(matrix, "fixed")


@pytest.mark.parametrize("bug,os_name,python", [
    ("python310", "ubuntu-latest", "3.10"),
    ("windows", "windows-latest", "3.12"),
    ("missing-data", "ubuntu-latest", "3.12"),
    ("entrypoint", "ubuntu-latest", "3.12"),
])
def test_removing_the_faults_required_environment_is_rejected(bug, os_name, python):
    matrix = plan(bug)
    matrix["include"].remove({"os": os_name, "python": python})
    with pytest.raises(ValueError, match="cannot expose"):
        validate_plan(matrix, bug)


def test_new_fault_without_a_declared_environment_fails_closed(monkeypatch):
    import matrix_plan

    monkeypatch.setattr(matrix_plan, "BUGS", (*matrix_plan.BUGS, "new-fault"))
    with pytest.raises(ValueError, match="every fixture"):
        plan("fixed")
