"""Configuration helpers.

Nothing spotifio needs in order to talk to Spotify has a built-in default. A
guessed value (a port, a host, a redirect URI) is rejected by Spotify with an
error the caller then has to debug, so values come from arguments or from the
environment and a missing one raises.
"""
import os

__all__ = ["load_dotenv", "require_env"]


def load_dotenv(path=".env"):
    """Load KEY=VALUE lines from a .env file into os.environ.

    Variables already in the environment win. Returns the number of variables
    set. This is not called automatically: importing spotifio never reads files
    behind your back.
    """
    if not os.path.exists(path):
        return 0
    count = 0
    with open(path) as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
                count += 1
    return count


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
