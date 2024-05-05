import pytest
from services.base import ServerUnavailable
from services.drop_sms_bot import DropSmsService
from aiohttp import ClientSession
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import WSGITransport
from main import app
import asyncio


class ResponseMock:
    def __init__(self, data, *args, **kwargs):
        self.data = data

    def __call__(self, *args, **kwargs):
        return self

    async def read(self):
        return self.data

    @property
    def content(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        pass



class ResponseMockCounter(ResponseMock):
    def __init__(self, data, *args, **kwargs):
        self.data = data
        self.counter = 0

    def __call__(self, *args, **kwargs):
        self.counter += 1
        return self



@pytest_asyncio.fixture
async def drop_sms(request):
    service = DropSmsService()
    await service.connect()
    yield service
    await service.close()



