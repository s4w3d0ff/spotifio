from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="spotifio",
    version="0.1.6",
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: AsyncIO",
    ],
    python_requires=">=3.7",
    install_requires=[
        "aiohttp>=3.8.0",
        "aiofiles>=0.8.0",
    ],
    keywords="spotify api async aiohttp music streaming oauth2",
    project_urls={
        "Bug Reports": "https://github.com/s4w3d0ff/spotifio/issues",
        "Source": "https://github.com/s4w3d0ff/spotifio",
    },
)
