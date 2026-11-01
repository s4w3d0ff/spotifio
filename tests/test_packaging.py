import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_VARS = ["SPOTIFIO_CLIENT_ID", "SPOTIFIO_CLIENT_SECRET",
                 "SPOTIFIO_REDIRECT_URI"]


def _requirements():
    lines = (ROOT / "requirements.txt").read_text().splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def test_requirements_txt_holds_the_security_floor():
    # aiohttp 3.14.3 and older are vulnerable to CVE-2026-111064 (OAuth callback
    # server) and CVE-2026-69244 (API requests). Lowering this floor reopens them.
    assert _requirements() == ["aiohttp>=3.14.4", "aiofiles>=24.1.0"]


def test_setup_py_has_no_second_dependency_list():
    setup_py = (ROOT / "setup.py").read_text()
    assert "open(\"requirements.txt\"" in setup_py
    assert "install_requires=install_requires" in setup_py
    assert "aiohttp>=" not in setup_py
    assert 'python_requires=">=3.10"' in setup_py


def test_env_example_lists_every_variable_the_library_requires():
    example = (ROOT / ".env.example").read_text()
    required = set()
    for path in (ROOT / "spotifio").rglob("*.py"):
        required.update(re.findall(r'require_env\("([A-Z_]+)"', path.read_text()))
    # SPOTIFIO_SCOPES is optional, so it is not found by the require_env search.
    assert required == set(REQUIRED_VARS)
    for name in sorted(required | {"SPOTIFIO_SCOPES"}):
        assert f"{name}=" in example, f"{name} is required but missing from .env.example"
