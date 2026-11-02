class SpotifyError(Exception):
    """Raised for non-2xx API responses. Carries the HTTP status and reason."""
    def __init__(self, status, reason, body=None):
        self.status = status
        self.reason = reason
        self.body = body or ""
        super().__init__(f"Request failed with status {status}: {reason} ({self.body})")


class ScopeError(Exception):
    """Raised before a request when the token lacks a scope the endpoint needs."""
