import os

import pytest

from spotifio.env import load_dotenv, require_env


@pytest.fixture
def clean_env():
    """No SPOTIFIO_ variable survives a test."""
    def drop():
        for name in list(os.environ):
            if name.startswith("SPOTIFIO_"):
                del os.environ[name]
    drop()
    yield
    drop()


def write_env(tmp_path, text):
    path = tmp_path / ".env"
    path.write_text(text)
    return str(path)


def test_a_normal_file_is_loaded(clean_env, tmp_path):
    path = write_env(tmp_path, "SPOTIFIO_CLIENT_ID=id\nSPOTIFIO_CLIENT_SECRET=secret\n")
    assert load_dotenv(path) == 2
    assert os.environ["SPOTIFIO_CLIENT_ID"] == "id"
    assert os.environ["SPOTIFIO_CLIENT_SECRET"] == "secret"


def test_a_missing_file_sets_nothing(clean_env, tmp_path):
    assert load_dotenv(str(tmp_path / "nope.env")) == 0


def test_a_variable_already_in_the_environment_wins(clean_env, tmp_path, monkeypatch):
    monkeypatch.setenv("SPOTIFIO_CLIENT_ID", "from_shell")
    load_dotenv(write_env(tmp_path, "SPOTIFIO_CLIENT_ID=from_file\n"))
    assert os.environ["SPOTIFIO_CLIENT_ID"] == "from_shell"


def test_comments_blank_lines_and_export_are_understood(clean_env, tmp_path):
    path = write_env(tmp_path, (
        "# a comment\n"
        "\n"
        "export SPOTIFIO_CLIENT_ID=id  # trailing comment\n"
        "SPOTIFIO_SCOPES=user-read-email user-read-private\n"
    ))
    assert load_dotenv(path) == 2
    assert os.environ["SPOTIFIO_CLIENT_ID"] == "id"
    assert os.environ["SPOTIFIO_SCOPES"] == "user-read-email user-read-private"


def test_quotes_are_stripped_once_and_only_the_quotes(clean_env, tmp_path):
    path = write_env(tmp_path, (
        'SPOTIFIO_CLIENT_SECRET="secret # not a comment"\n'
        "SPOTIFIO_REDIRECT_URI='http://127.0.0.1:5050/cb'\n"
    ))
    load_dotenv(path)
    assert os.environ["SPOTIFIO_CLIENT_SECRET"] == "secret # not a comment"
    assert os.environ["SPOTIFIO_REDIRECT_URI"] == "http://127.0.0.1:5050/cb"


def test_a_line_that_is_not_an_assignment_names_the_file_and_line(clean_env, tmp_path):
    path = write_env(tmp_path, "SPOTIFIO_CLIENT_ID=id\nthis is not config\n")
    with pytest.raises(ValueError) as exc:
        load_dotenv(path)
    assert ".env:2" in str(exc.value)
    assert "this is not config" in str(exc.value)


def test_a_quote_that_never_closes_is_an_error(clean_env, tmp_path):
    path = write_env(tmp_path, 'SPOTIFIO_CLIENT_SECRET="abc\n')
    with pytest.raises(ValueError) as exc:
        load_dotenv(path)
    assert "never closes it" in str(exc.value)


def test_junk_after_a_closing_quote_is_an_error(clean_env, tmp_path):
    path = write_env(tmp_path, 'SPOTIFIO_CLIENT_SECRET="abc" trash\n')
    with pytest.raises(ValueError) as exc:
        load_dotenv(path)
    assert "trash" in str(exc.value)


def test_a_variable_name_with_a_space_in_it_is_an_error(clean_env, tmp_path):
    path = write_env(tmp_path, "SPOTIFIO CLIENT ID=id\n")
    with pytest.raises(ValueError) as exc:
        load_dotenv(path)
    assert "not a valid variable name" in str(exc.value)


def test_two_variables_glued_onto_one_line_are_rejected(clean_env, tmp_path):
    # A .env file whose last line has no newline glues the next variable onto it.
    # Loading that silently stores a broken secret.
    path = write_env(tmp_path, "SPOTIFIO_CLIENT_SECRET=abcSPOTIFIO_SCOPES=user-read-email\n")
    with pytest.raises(ValueError) as exc:
        load_dotenv(path)
    assert "own line" in str(exc.value)


def test_require_env_raises_naming_the_variable(clean_env, monkeypatch):
    monkeypatch.delenv("SPOTIFIO_CLIENT_ID", raising=False)
    with pytest.raises(ValueError) as exc:
        require_env("SPOTIFIO_CLIENT_ID", hint="Get it from the Spotify dashboard.")
    assert "SPOTIFIO_CLIENT_ID is not set" in str(exc.value)
    assert "Get it from the Spotify dashboard." in str(exc.value)


def test_require_env_returns_the_value(clean_env, monkeypatch):
    monkeypatch.setenv("SPOTIFIO_CLIENT_ID", "id")
    assert require_env("SPOTIFIO_CLIENT_ID") == "id"
