import asyncio
from typing import Callable, Optional
import requests
from base import BaseService
from abc import ABC, abstractmethod



class DropSmsService(BaseService):
    '''Service implementation for DropSms'''

    api = '95a7ea60-6e3a-47e2-9314-015e969956d0'

    country_dict = {
        'Russia': 0,
        'Ukraine': 1,
        'Kazakhstan': 2,
        'China': 3,
        'Philippines': 4,
        'Myanmar': 5,
        'Indonesia': 6,
        'Malaysia': 7,
        'Kenya': 8,
        'Tanzania': 9,
        'Vietnam': 10,
        'Kyrgyzstan': 11,
        'USA': 12,
        'Israel': 13,
        'Hong Kong': 14,
        'Poland': 15,
        'Great Britain': 16,
        'Madagascar': 17,
        'Congo': 18,
        'Nigeria': 19,
        'Macau': 20,
        'Egypt': 21,
        'India': 22,
        'Ireland': 23,
        'Cambodia': 24,
        'Laos': 25,
        'Haiti': 26,
        'Ivory Coast': 27,
        'The Gambia': 28,
        'Serbia': 29,
        'Yemen': 30,
        'South Africa': 31,
        'Romania': 32,
        'Colombia': 33,
        'Estonia': 34,
        'Azerbaijan': 35,
        'Canada': 36,
        'Morocco': 37,
        'Ghana': 38,
        'Argentina': 39,
        'Uzbekistan': 40,
        'Cameroon': 41,
        'Chad': 42,
        'Germany': 43,
        'Lithuania': 44,
        'Croatia': 45,
        'Sweden': 46,
        'Iraq': 47,
        'The Netherlands': 48,
        'Latvia': 49,
        'Austria': 50,
        'Belarus': 51,
        'Thailand': 52,
        'Saudi Arabia': 53,
        'Mexico': 54,
        'Taiwan': 55,
        'Spain': 56,
        'Iran': 57,
        'Algeria': 58,
        'Slovenia': 59,
        'Bangladesh': 60,
        'Senegal': 61,
        'Turkey': 62,
        'Czech Republic': 63,
        'Sri Lanka': 64,
        'Peru': 65,
        'Pakistan': 66,
        'New Zealand': 67,
        'Guinea': 68,
        'Mali': 69,
        'Venezuela': 70,
        'Ethiopia': 71,
        'Mongolia': 72,
        'Brazil': 73,
        'Afghanistan': 74,
        'Uganda': 75,
        'Angola': 76,
        'Cyprus': 77,
        'France': 78,
        'Papua New Guinea': 79,
        'Mozambique': 80,
        'Nepal': 81,
        'Belgium': 82,
        'Bulgaria': 83,
        'Hungary': 84,
        'Moldova': 85,
        'Italy': 86,
        'Paraguay': 87,
        'Honduras': 88,
        'Tunisia': 89,
        'Nicaragua': 90,
        'East Timor': 91,
        'Bolivia': 92,
        'Costa Rica': 93,
        'Guatemala': 94,
        'UAE': 95,
        'Zimbabwe': 96,
        'Puerto Rico': 97,
        'Sudan': 98,
        'Togo': 99,
        'Kuwait': 100,
        'El Salvador': 101,
        'Libya': 102,
        'Jamaica': 103,
        'Trinidad and Tobago': 104,
        'Ecuador': 105,
        'Eswatini': 106,
        'Oman': 107,
        'Bosnia and Herzegovina': 108,
        'Dominican Republic': 109,
        'Syria': 110,
        'Qatar': 111,
        'Panama': 112,
        'Cuba': 113,
        'Mauritania': 114,
        'Sierra Leone': 115,
        'Jordan': 116,
        'Portugal': 117,
        'Barbados': 118,
        'Burundi': 119,
        'Benin': 120,
        'Botswana': 123,
        'Georgia': 128,
        'Greece': 129,
        'Guinea-Bissau': 130,
        'Guyana': 131,
        'Saint Kitts and Nevis': 134,
        'Liberia': 135,
        'Lesotho': 136,
        'Malawi': 137,
        'Namibia': 138,
        'Rwanda': 140,
        'Slovakia': 141,
        'Suriname': 142,
        'Tajikistan': 143,
        'Bahrain': 145,
        'Reunion': 146,
        'Zambia': 147,
        'Armenia': 148,
        'Somalia': 149,
        'Chile': 151,
        'Burkina Faso': 152,
        'Gabon': 154,
        'Albania': 155,
        'Uruguay': 156,
        'Mauritius': 157,
        'Bhutan': 158,
        'Maldives': 159,
        'Guadeloupe': 160,
        'Turkmenistan': 161,
        'French Guiana': 162,
        'Finland': 163,
        'Saint Lucia': 164,
        'Luxembourg': 165,
        'Saint Vincent and the Grenadines': 166,
        'Equatorial Guinea': 167,
        'Djibouti': 168,
        'Antigua and Barbuda': 169,
        'Cayman Islands': 170,
        'Montenegro': 171,
        'Switzerland': 173,
        'Norway': 174,
        'Australia': 175,
        'Eritrea': 176,
        'South Sudan': 177,
        'Sao Tome and Principe': 178,
        'Aruba': 179,
        'Montserrat': 180,
        'Anguilla': 181,
        'Japan': 182,
        'North Macedonia': 183,
        'Seychelles': 184,
        'New Caledonia': 185,
        'Cape Verde': 186,
        'South Korea': 200
    }

    services_dict = {
        'Facebook': 1,
        'WhatsApp': 2,
        'VK': 3,
        'Google': 4,
        'Instagram': 5
    }

    async def get_balance(self) -> int:
        url = f'https://api.dropsms.cc/stubs/handler_api.php?action=getBalance&api_key={self.api}'
        r = requests.get(url=url).text
        return r

    async def get_countries(self) -> dict[str, int]:
        return self.country_dict

    async def get_services(self) -> dict[str, int]:
        return self.services_dict

    async def rent_number(self, country_name: str, service_name: str, handler: Optional[Callable[[str], None]], *args,
                          **kwargs):
        if country_name in self.country_dict and service_name in self.services_dict:
            country_id = self.country_dict[country_name]
            service_id = self.services_dict[service_name]
            url = f"https://api.dropsms.cc/stubs/handler_api.php?action=getNumber&api_key={self.api}&service={service_id}&country={country_id}"
            r = requests.get(url=url).text
            if handler:
                await handler(r)  # Внесем изменение здесь
            return r
        else:
            raise ValueError("Страна или сервис не найден")


service = DropSmsService()
async def main():
    balance = await service.get_balance()
    print("Баланс:", balance)

    async def handler(response):
        print("Ответ от сервера:", response)

    country_id = 'Russia'
    service_id = 'Google'
    await service.rent_number(country_id, service_id, handler)


asyncio.run(main())