"""Configuration helpers.

Nothing spotifio needs in order to talk to Spotify has a built-in default. A
guessed value (a port, a host, a redirect URI) is rejected by Spotify with an
error the caller then has to debug, so values come from arguments or from the
environment and a missing one raises.
"""
import os
import re

__all__ = ["load_dotenv", "require_env"]

_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_TRAILING_COMMENT = re.compile(r"\s+#")


def load_dotenv(path=".env"):
    """Load KEY=VALUE into os.environ. Existing vars win. Bad lines raise ValueError with path:lineno. Not automatic."""
    if not os.path.exists(path):
        return 0
    count = 0
    with open(path) as file:
        for lineno, raw_line in enumerate(file, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            location = f"{path}:{lineno}"
            key, separator, value = line.partition("=")
            if not separator:
                raise ValueError(f"{location}: not a KEY=VALUE line: {line!r}")
            key = key.removeprefix("export ").strip()
            if not _NAME.match(key):
                raise ValueError(f"{location}: {key!r} is not a valid variable name")
            value = _clean_value(value.strip(), location)
            if key not in os.environ:
                os.environ[key] = value
                count += 1
    return count


def _clean_value(value, location):
    """Take the value a shell would take: one pair of quotes, no trailing comment."""
    if value[:1] in ("'", '"'):
        quote = value[0]
        end = value.find(quote, 1)
        if end == -1:
            raise ValueError(f"{location}: the value starts with {quote} and never closes it")
        trailing = value[end + 1:].strip()
        if trailing and not trailing.startswith("#"):
            raise ValueError(f"{location}: {trailing!r} follows a quoted value and is not a comment")
        return value[1:end]
    _reject_glued_variables(value, location)
    return _TRAILING_COMMENT.split(value, maxsplit=1)[0].strip()


def _reject_glued_variables(value, location):
    """A value holding another spotifio variable means the file's lines were joined. Reject instead of storing a broken secret."""
    if "SPOTIFIO_" in value:
        raise ValueError(
            f"{location}: the value contains another SPOTIFIO_ variable. Each variable "
            "needs its own line, and the file must end with a newline, or the lines are "
            "read as one."
        )


def require_env(name, hint=""):
    """Return os.environ[name] or raise ValueError naming what is missing."""
    value = os.environ.get(name)
    if not value:
        raise ValueError(
            f"{name} is not set. Pass it as an argument or set {name} in your "
            f"environment (a .env file works with spotifio.load_dotenv()). "
            f"spotifio has no default for it. {hint}"
        )
    return value
