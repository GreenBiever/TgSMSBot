import asyncio
import logging

from services.base import BaseService, ServerUnavailable, BadAPIKey
from typing import Callable
from config import config
import aiohttp
import json
import datetime as dt
from . import sms_activation_countries, sms_activation_services

logger = logging.getLogger(__name__)


class SmsActivationPro(BaseService):
    MAX_CACHING_TIME = 12  # in hours
    api_key = config['api_keys']['sms_activation']
    _api_url = 'https://receivesms.store/stubs/handler_api.php'
    _handlers: dict[int, tuple[Callable, list, dict]] = {}

    def __init__(self):
        self._countries = sms_activation_countries.countries
        self._services = sms_activation_services.services

    async def connect(self):
        connector = aiohttp.TCPConnector(ssl=False)
        self.aiohttp_session = aiohttp.ClientSession(connector=connector)


    async def get_balance(self) -> float:
        payload = {'api_key': self.api_key, 'action': 'getBalance'}
        async with self.aiohttp_session.get(self._api_url, params=payload) as response:
            data = (await response.content.read()).decode()
            if data == 'BAD_KEY':
                raise BadAPIKey
            args = data.split(':')
            if args[0] == 'ACCESS_BALANCE':
                return float(args[1])
            else:
                raise ServerUnavailable("Server response not correct")

    async def get_countries(self) -> dict[str, str]:
        return self._countries

    async def get_services(self) -> dict[str, str]:
        return self._services

    async def close(self):
        await self.aiohttp_session.close()

    async def get_price(self, country_id: str, service_id: str) -> dict:
        cost = None
        count = None
        return cost

    async def rent_number(self, country_id: str, service_id: str, handler: Callable[[str], None], *args,
                          **kwargs) -> str:
        if not (country_id in (await self.get_countries()).values() and service_id in (
                await self.get_services()).values()):
            raise ValueError('Unsupported country_id or value_id')
        payload = {'api_key': self.api_key, 'action': 'getNumber', 'service': service_id, 'country': country_id}
        async with self.aiohttp_session.get(self._api_url, params=payload) as response:
            response_text = await response.text()
            if response_text.startswith("ACCESS_NUMBER:"):
                parts = response_text.split(":")
                activation_id = parts[1]
                phone_number = parts[2]
            elif response_text.startswith("NO_BALANCE"):
                raise ServerUnavailable("Нет Баланса!")
            else:
                raise ServerUnavailable
        self._handlers[activation_id] = (handler, args, kwargs)
        return phone_number

    def __str__(self):
        return 'SMS Activation Pro'


