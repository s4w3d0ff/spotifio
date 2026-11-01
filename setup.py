from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# requirements.txt is the one place a dependency floor is written; reading it here
# keeps a pinned install and a PyPI install asking for the same thing.
with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = [
        line.strip() for line in fh
        if line.strip() and not line.strip().startswith("#")
    ]

setup(
    name="spotifio",
    version="0.2.0",
    author="s4w3d0ff",
    author_email="",
    description="An async Spotify Web API client library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/s4w3d0ff/spotifio",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: AsyncIO",
    ],
    # aiohttp 3.14.4 needs Python 3.10 or newer.
    python_requires=">=3.10",
    install_requires=install_requires,
    keywords="spotify api async aiohttp music streaming oauth2",
    project_urls={
        "Bug Reports": "https://github.com/s4w3d0ff/spotifio/issues",
        "Source": "https://github.com/s4w3d0ff/spotifio",
    },
)
