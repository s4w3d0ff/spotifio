import os
import json
import aiofiles
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class TokenStorage(ABC):        
    @abstractmethod
    async def save_token(self, token):
        pass
        
    @abstractmethod
    async def load_token(self):
        pass


class FakeStorage(TokenStorage):
    async def save_token(self, token):
        logger.error(f"[FakeStorage] Fake save_token triggered!")

    async def load_token(self):
        logger.error(f"[FakeStorage] Fake load_token triggered!")


class JSONStorage(TokenStorage):
    def __init__(self, storage_dir='db'):
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            logger.warning(f"Created dir {self.storage_dir}")

    async def _load(self, filename):
        async with aiofiles.open(filename, 'r') as file:
            content = await file.read()
            return json.loads(content)

    async def _save(self, data, filename):
        async with aiofiles.open(filename, 'w') as file:
            await file.write(json.dumps(data, indent=4))

    async def save_token(self, token, name=''):
        """ Saves OAuth token to database"""
        file_path = os.path.join(self.storage_dir, name+"_token.json")
        await self._save(token, file_path)
        logger.warning(f"Token saved at: {file_path}")

    async def load_token(self, name=''):
        """ Gets saved OAuth token from database"""
        file_path = os.path.join(self.storage_dir, name+"_token.json")
        if not os.path.exists(file_path):
            logger.warning(f"No token at: {file_path}")
            return None
        return await self._load(file_path)