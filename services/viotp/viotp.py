from services.base import BaseService, ServerUnavailable, BadAPIKey
from typing import Callable
from config import config
import aiohttp
import json
import datetime as dt


class ViotpService(BaseService):
    MAX_CACHING_TIME = 12  # in hours
    api_key = config['api_keys']['viotp']
    _api_url = 'https://api.viotp.com/'
    _handlers: dict[int, tuple[Callable, list, dict]] = {}

    def __init__(self):
        self._services = {}
        self.aiohttp_session = aiohttp.ClientSession()

    async def get_balance(self) -> int:
        url = self._api_url + 'users/balance'
        payload = {'token': self.api_key}
        async with self.aiohttp_session.get(url, params=payload) as response:
            data = await response.json()
            if 'status_code' in data and data['status_code'] == 200:
                balance = data.get('data', {}).get('balance')
                if balance is not None:
                    return int(balance)
                else:
                    raise ServerUnavailable("Balance data not found in server response")
            elif 'status_code' in data and data['status_code'] == 401:
                raise BadAPIKey("Wrong API key")
            else:
                raise ServerUnavailable("Server response not correct")

    async def get_services(self) -> dict[str, str]:
        if not hasattr(self, 'last_services_update_time'):
            self.last_services_update_time = dt.datetime(year=2000, month=1, day=1)
        if dt.datetime.now() - self.last_services_update_time < dt.timedelta(hours=self.MAX_CACHING_TIME):
            return self._services
        self.last_services_update_time = dt.datetime.now()
        url = self._api_url + 'service/get'
        payload = {'token': self.api_key}
        async with self.aiohttp_session.get(url, params=payload) as response:
            data = await response.json()
        if 'status_code' in data and data['status_code'] == 200:
            services = {service['name']: str(service['id']) for service in data['data']}
            self._services = services
            return services
        elif 'status_code' in data and data['status_code'] == 401:
            raise BadAPIKey("Wrong API key")
        else:
            raise ServerUnavailable("Server response not correct")

    async def rent_number(self, service_id: str, handler: Callable[[str], None], *args, **kwargs):
        if not service_id in (await self.get_services()).values():
            raise ValueError('Unsupported country_id or value_id')
        url = self._api_url + 'request/get'
        payload = {'token': self.api_key, 'serviceId': service_id}
        async with self.aiohttp_session.get(url, params=payload) as response:
            response = await response.content.read()
            try:
                data = json.loads(response)
                activation_id = data['request_id']
            except (json.JSONDecodeError, KeyError):
                raise ServerUnavailable
        self._handlers[activation_id] = (handler, args, kwargs)
        return data['phone_number']

    async def get_countries(self) -> None:
        return None


    async def get_price(self, country_id: str, service_id: str) -> int:
        url = 'https://api.viotp.com/service/getv2'
        payload = {'token': self.api_key, 'country': country_id}
        async with self.aiohttp_session.get(url, params=payload) as response:
            response_text = await response.text()
            try:
                data = json.loads(response_text)
                for item in data.get('data', []):
                    if str(item.get('id')) == service_id:
                        return int(item.get('price', 0))
                raise ServerUnavailable("Сервис не найден")
            except json.JSONDecodeError:
                raise ServerUnavailable

