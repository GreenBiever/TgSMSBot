import asyncio
from typing import Callable, Optional
from aiogram.client.session import aiohttp
from base import BaseService
from abc import ABC, abstractmethod



class Viotp(BaseService):
    api = 'c54999fc895f48b99a8b53f395fe5907'

    async def get_balance(self) -> str:
        url = f'https://api.viotp.com/users/balance?token={self.api}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()

    async def get_countries(self) -> None:
        return None


    async def get_services(self) -> dict[str, int]:
        url = f'https://api.viotp.com/service/get?token={self.api}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                services_data = await response.json()

        service_dict = {}

        for service in services_data['data']:
            service_dict[service['name']] = service['id']

        return service_dict

    async def rent_number(self, service_name: str, handler: Optional[Callable[[str], None]], *args, **kwargs):
        services = await self.get_services()
        if service_name in services:
            service_id = services[service_name]
            print(service_id)
            url = f'https://api.viotp.com/request/get?token={self.api}&serviceId={service_id}'
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    r = await response.json()
                    status = r.get('status_code')
                    print("JSON с Сайта: ", r)
                    if status == 200:
                        phone_number = r.get('data', {}).get('phone_number')
                        if phone_number and handler:
                            handler(phone_number)
                        return phone_number
                    elif status == 401:
                        raise ValueError("Неверный токен")
                    elif status == 429:
                        raise ValueError("Превышен лимит запросов")
                    elif status == -1:
                        raise ValueError("Ошибка")
                    elif status == -2:
                        raise ValueError("Недостаточно средств на балансе")
                    elif status == -3:
                        raise ValueError("Банк номеров временно отсутствует, обратитесь в службу поддержки")
                    elif status == -4:
                        raise ValueError("Неверный идентификатор сервиса или сервис находится на обслуживании")
                    else:
                        print(f"Статус ответа: {status}, неизвестная ошибка")
        else:
            raise ValueError("Услуга не найдена")



service = Viotp()


async def main():
    balance = await service.get_balance()
    print("Баланс: ", balance)

    services = await service.get_services()
    print("Сервисы: ", services)

    async def handler(response):
        print("Ответ от сервера:", response)

    service_name = 'Telegram'
    r = await service.rent_number(service_name, handler)
    print(r)


asyncio.run(main())