from services.base import BaseService, ServerUnavailable, BadAPIKey
from typing import Callable
from config import config
import aiohttp
import json
import datetime as dt


class SmsManServices(BaseService):
    '''SMS Man service implementation'''

    MAX_CACHING_TIME = 12  # in hours
    api_key = config['api_keys']['sms_man']
    _api_url = 'https://api.sms-man.com/control/'
    _handlers: dict[int, tuple[Callable, list, dict]] = {}

    def __init__(self):
        self._countries = {}
        self._services = {}
        self.aiohttp_session = aiohttp.ClientSession()

    async def get_balance(self) -> int:
        url = f'{self._api_url}get-balance'
        payload = {'token': self.api_key}
        async with self.aiohttp_session.get(self._api_url, params=payload) as response:
            data = (await response.content.read()).decode()
            if 'success' in data and data['success'] == False:
                error_code = data.get('error_code', 'unknown_error')
                error_msg = data.get('error_msg', 'Unknown error occurred.')
                if error_code == 'wrong_token':
                    raise BadAPIKey(error_msg)
                else:
                    raise ServerUnavailable("Server response not correct")
            elif 'balance' in data:
                return float(data['balance'])
            else:
                raise ServerUnavailable("Unexpected server response format.")

    async def get_countries(self) -> dict[str, str]:
        if not hasattr(self, 'last_countries_update_time'):
            self.last_countries_update_time = dt.datetime(year=2000, month=1, day=1)
        if dt.datetime.now() - self.last_countries_update_time < dt.timedelta(hours=self.MAX_CACHING_TIME):
            return self._countries
        self.last_countries_update_time = dt.datetime.now()
        url = f'{self._api_url}countries'
        payload = {'token': self.api_key}
        async with self.aiohttp_session.get(url, params=payload) as response:
            data = await response.json()
            if 'success' in data and not data['success']:
                error_code = data.get('error_code', 'unknown_error')
                error_msg = data.get('error_msg', 'Unknown error occurred.')
                if error_code == 'wrong_token':
                    raise BadAPIKey(error_msg)
                else:
                    raise ServerUnavailable("Server response not correct")
            try:
                countries = {country['title']: str(country['id']) for country in data}
                self._countries = countries
                return countries
            except (KeyError, TypeError):
                raise ServerUnavailable("Server response not correct")

    async def get_services(self) -> dict[str, str]:
        if not hasattr(self, 'last_services_update_time'):
            self.last_services_update_time = dt.datetime(year=2000, month=1, day=1)
        if dt.datetime.now() - self.last_services_update_time < dt.timedelta(hours=self.MAX_CACHING_TIME):
            return self._services
        self.last_services_update_time = dt.datetime.now()
        url = f'{self._api_url}applications'
        payload = {'token': self.api_key}
        async with self.aiohttp_session.get(url, params=payload) as response:
            data = await response.content.read()
            try:
                data = json.loads(data)
                if isinstance(data, list):
                    services = {service['name']: str(service['id']) for service in data}
                    self._services = services
                    return services
                elif isinstance(data, dict) and 'success' in data and not data['success']:
                    error_code = data.get('error_code', 'unknown_error')
                    error_msg = data.get('error_msg', 'Unknown error occurred.')
                    if error_code == 'wrong_token':
                        raise BadAPIKey(error_msg)
                    else:
                        raise ServerUnavailable("Server response not correct")
                else:
                    raise ServerUnavailable("Server response not correct")
            except (KeyError, TypeError, json.JSONDecodeError):
                raise ServerUnavailable("Server response not correct")

    def close(self):
        return self.session.close()

    async def rent_number(self, country_id: str, service_id: str, handler: Callable[[str], None], *args, **kwargs):
        if not (country_id in (await self.get_countries()).values() and service_id in (await self.get_services()).values()):
            raise ValueError('Unsupported country_id or value_id')
        url = f'{self._api_url}get-number'
        payload = {'token': self.api_key, 'country_id': country_id, 'application_id': service_id}
        async with self.aiohttp_session.get(self._api_url, params=payload) as response:
            response = await response.content.read()
            try:
                data = json.loads(response)
                activationId = data['request_id']
                phone_number = data['number']
            except (json.JSONDecodeError, KeyError):
                raise ServerUnavailable
        self._handlers[activationId] = (handler, args, kwargs)
        return phone_number
