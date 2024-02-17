from .base import BaseService
from .sms_activate import SMSActivateService
import json

FILEPATH = r'C:\Users\vn264\Desktop\sms_bot\services\services.json'

services: list[BaseService] = [SMSActivateService()]  # Ordered by priority

with open(FILEPATH, 'r', encoding='utf-8') as fp:
    data = json.load(fp)
all_services: list[str] = data['all_services']
all_countries: list[str] = data['all_countries']