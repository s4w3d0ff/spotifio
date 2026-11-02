import json
import logging
import os
import tempfile

import aiofiles
import aiofiles.os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class TokenStorage(ABC):
    @abstractmethod
    async def save_token(self, token, name=''):
        """Store an OAuth token under `name`."""

    @abstractmethod
    async def load_token(self, name=''):
        """Return the token stored under `name`, or None when there is none."""


class JSONStorage(TokenStorage):
    """One JSON file per token name inside storage_dir."""

    def __init__(self, storage_dir='db'):
        self.storage_dir = storage_dir
        created = not os.path.exists(self.storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        if created:
            # the token dir belongs to the owner
            os.chmod(self.storage_dir, 0o700)
            logger.warning(f"Created dir {self.storage_dir}")

    async def _load(self, filename):
        async with aiofiles.open(filename, 'r') as file:
            return json.loads(await file.read())

    async def _save(self, data, filename):
        # mkstemp is 0600 at birth, rename is atomic, a symlink at the target is
        # replaced not followed
        directory = os.path.dirname(filename) or '.'
        descriptor, temp_path = tempfile.mkstemp(dir=directory, prefix='.token_')
        os.close(descriptor)
        try:
            async with aiofiles.open(temp_path, 'w') as file:
                await file.write(json.dumps(data, indent=4))
            await aiofiles.os.replace(temp_path, filename)
        except BaseException:
            await aiofiles.os.remove(temp_path)
            raise

    async def save_token(self, token, name=''):
        """Save an OAuth token to <storage_dir>/<name>_token.json."""
        await self._save(token, self._path(name))
        logger.warning(f"Token saved at: {self._path(name)}")

    async def load_token(self, name=''):
        """Read the OAuth token back, or return None when nothing is stored."""
        file_path = self._path(name)
        if not os.path.exists(file_path):
            logger.warning(f"No token at: {file_path}")
            return None
        return await self._load(file_path)

    def _path(self, name):
        return os.path.join(self.storage_dir, name + "_token.json")
