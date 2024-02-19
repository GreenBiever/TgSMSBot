import json
from services import services
import asyncio


FILEPATH = r'C:\Users\vn264\Desktop\sms_bot\services\services.json'

async def load():
    '''Load all services and countries'''
    all_services = []
    all_countries = []
    for service in services:
        if hasattr(service, 'connect'):
            await service.connect()    
    for service in services:
        data = await service.get_services()
        for service_name in data.keys():
            if service_name not in all_services:
                all_services.append(service_name)
        data = await service.get_countries()
        for country_name in data.keys():
            if country_name not in all_countries:
                all_countries.append(country_name)
    with open(FILEPATH, 'w+', encoding='utf-8') as fp:
        json.dump({'all_services': all_services, 'all_countries': all_countries}, fp)

if __name__ == '__main__':
    asyncio.run(load())