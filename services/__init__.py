from .base import BaseService
from .sms_activate import SMSActivateService
from .DropSmsBot import DropSmsService


services: list[BaseService] = [SMSActivateService(), DropSmsService()]  # Ordered by priority