import json

import pytest

from soup_release_lab import __version__
from soup_release_lab.cli import main
from soup_release_lab.core import validate_name, validate_workers


@pytest.mark.parametrize("value", [True, False, "3", None, 2.0])
def test_worker_type(value):
    with pytest.raises(ValueError, match="integer"):
        validate_workers(value)


@pytest.mark.parametrize("value", [-1, 0, 17])
def test_worker_bounds(value):
    with pytest.raises(ValueError, match="between"):
        validate_workers(value)


@pytest.mark.parametrize("value", [None, 4, "", "  "])
def test_name_validation(value):
    with pytest.raises(ValueError, match="non-empty"):
        validate_name(value)


@pytest.mark.parametrize("workers", [1, 16])
def test_valid_bounds(workers):
    assert validate_workers(workers) == workers


def test_configuration(tmp_path, capsys):
    config = tmp_path / "service with spaces.toml"
    config.write_text('[service]\nname=" caf\u00e9 "\nworkers=3\n', encoding="utf-8")
    assert main(["inspect", str(config)]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "name": "caf\u00e9", "workers": 3, "profile": "safe", "schema": 1,
    }


def test_default_workers(tmp_path, capsys):
    config = tmp_path / "service.toml"
    config.write_text('[service]\nname="example"\n', encoding="utf-8")
    assert main(["inspect", str(config)]) == 0
    assert json.loads(capsys.readouterr().out)["workers"] == 1


@pytest.mark.parametrize("content", [
    'broken [', '[other]\nname="x"', '[service]\nname="x"\nworkers=0',
])
def test_configuration_errors(tmp_path, capsys, content):
    config = tmp_path / "invalid.toml"
    config.write_text(content, encoding="utf-8")
    assert main(["inspect", str(config)]) == 2
    assert "soup-check:" in capsys.readouterr().err


def test_missing_file(tmp_path, capsys):
    assert main(["inspect", str(tmp_path / "absent.toml")]) == 2
    assert "soup-check:" in capsys.readouterr().err


@pytest.mark.parametrize("option", ["--help", "--version"])
def test_cli_information(option, capsys):
    with pytest.raises(SystemExit) as result:
        main([option])
    assert result.value.code == 0
    output = capsys.readouterr().out
    assert "soup-check" in output
    if option == "--version":
        assert __version__ in output


def test_missing_command():
    with pytest.raises(SystemExit) as result:
        main([])
    assert result.value.code == 2

