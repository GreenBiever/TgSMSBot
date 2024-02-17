import asyncio
from services.base import BaseService, ServerUnavailable, BadAPIKey
from typing import Callable
from config import config
import aiohttp
import json
import datetime as dt
from services.drop_sms_bot import drop_sms_services, drop_sms_countries


class DropSmsService(BaseService):

    MAX_CACHING_TIME = 12  # in hours
    api_key = config['api_keys']['drop_sms']
    _api_url = 'https://api.dropsms.cc/stubs/handler_api.php'
    _handlers: dict[int, tuple[Callable, list, dict]] = {}

    def __init__(self):
        self._countries = drop_sms_countries.countries
        self._services = drop_sms_services.services
        self.aiohttp_session = aiohttp.ClientSession()

    async def connect(self):
        self.aiohttp_session = aiohttp.ClientSession()

    async def get_balance(self) -> int:
        payload = {'action': 'getBalance', 'api_key': self.api_key}
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

    def close(self):
        return self.aiohttp_session.close()

    async def get_price(self, country_id: str, service_id: str) -> int:
        pass

    async def rent_number(self, country_id: str, service_id: str, handler: Callable[[str, str], None], *args,
                          **kwargs) -> str:
        if not (country_id in (await self.get_countries()).values() and service_id in (
                await self.get_services()).values()):
            raise ValueError('Unsupported country_id or value_id')
        payload = {'action': 'getNumber', 'api_key': self.api_key, 'service': service_id, 'country': country_id}
        async with self.aiohttp_session.get(self._api_url, params=payload) as response:
            response_text = await response.text()
            if not response_text:
                raise ServerUnavailable("Empty response from server")
            try:
                data = json.loads(response_text)
                if 'response' in data and data['response'] == 'NO_BALANCE':
                    raise ServerUnavailable("Insufficient balance to rent number")
                activation_id = data['activationId']
            except (json.JSONDecodeError, KeyError):
                raise ServerUnavailable
        self._handlers[activation_id] = (handler, (activation_id,) + args, kwargs)
        return data['phoneNumber']


    async def check_sms_status(self, idActivate: str):
        while True:
            await asyncio.sleep(180)
            payload = {'action': 'getStatus', 'api_key': self.api_key, 'id': idActivate}
            async with self.aiohttp_session.get(self._api_url, params=payload) as response:
                response_text = await response.text()

    def __str__(self):
        return 'Drop SMS'
