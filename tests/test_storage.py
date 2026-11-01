import os

import pytest

from spotifio.storage import JSONStorage, TokenStorage


@pytest.fixture
def storage_dir(tmp_path):
    return str(tmp_path / "db")


async def test_token_round_trip(storage_dir):
    storage = JSONStorage(storage_dir=storage_dir)
    token = {"access_token": "a", "refresh_token": "r", "expires_time": 1}
    await storage.save_token(token, name="spotify")
    assert await storage.load_token(name="spotify") == token


async def test_token_file_is_readable_by_the_owner_only(storage_dir):
    storage = JSONStorage(storage_dir=storage_dir)
    await storage.save_token({"access_token": "a"}, name="spotify")
    mode = os.stat(os.path.join(storage_dir, "spotify_token.json")).st_mode
    assert mode & 0o777 == 0o600


async def test_storage_dir_is_owner_only_when_spotifio_creates_it(storage_dir):
    JSONStorage(storage_dir=storage_dir)
    assert os.stat(storage_dir).st_mode & 0o777 == 0o700


async def test_a_symlink_at_the_token_path_is_replaced_not_followed(tmp_path):
    storage_dir = str(tmp_path / "db")
    outside = tmp_path / "someone_elses_file"
    outside.write_text("keep me")
    storage = JSONStorage(storage_dir=storage_dir)
    os.symlink(str(outside), os.path.join(storage_dir, "spotify_token.json"))
    await storage.save_token({"access_token": "a"}, name="spotify")
    assert outside.read_text() == "keep me"
    assert await storage.load_token(name="spotify") == {"access_token": "a"}


async def test_a_missing_token_is_None_not_a_crash(storage_dir):
    assert await JSONStorage(storage_dir=storage_dir).load_token(name="spotify") is None


def test_token_storage_needs_both_methods():
    class HalfStorage(TokenStorage):
        async def load_token(self, name=''):
            return None

    with pytest.raises(TypeError):
        HalfStorage()


def test_json_storage_matches_the_token_storage_interface():
    assert issubclass(JSONStorage, TokenStorage)
