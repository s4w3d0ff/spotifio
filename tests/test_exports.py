import spotifio
from spotifio import Client, RequestHandler, SpotifyError, TokenHandler


def test_star_import_exports_error_type():
    names = [n for n in dir(spotifio) if not n.startswith("_")]
    assert "SpotifyError" in names


def test_spotify_error_carries_status_reason_body():
    err = SpotifyError(404, "resource not found", '{"error":{"status":404}}')
    assert err.status == 404
    assert err.reason == "resource not found"
    assert err.body == '{"error":{"status":404}}'
    assert isinstance(err, Exception)
    assert "Request failed with status 404: resource not found" in str(err)


def test_error_body_defaults_to_empty():
    assert SpotifyError(500, "boom").body == ""


def test_client_is_a_request_handler():
    assert issubclass(Client, RequestHandler)
    assert hasattr(TokenHandler, "stop")
