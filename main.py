from aiogram import Bot, Dispatcher, types, F
from aiogram.exceptions import TelegramBadRequest
from contextlib import asynccontextmanager
from config import config
from handlers import info, admin
import logging
from services.sms_activate.webhook_router import router as sms_activate_webhook_router
from fastapi import FastAPI
import uvicorn
from services import services
from database.connect import engine


logging.basicConfig(level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

logger = logging.getLogger(__name__)
bot = Bot(config['Telegram']['bot_token'], parse_mode='HTML')
dp = Dispatcher()
dp.include_routers(info.router, admin.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    #if (await bot.get_webhook_info()) != WEBHOOK_URL:
    await bot.set_webhook(url=(config['web_server']['webhook_url'] +
                              config['web_server']['tg_webhook_path'] ), allowed_updates=['*'])
    for service in services:
        if hasattr(service, 'connect'):
            await service.connect()
    yield
    for service in services:
        if hasattr(service, 'close'):
            await service.close()
    await bot.session.close()
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(sms_activate_webhook_router)

@app.post(config['web_server']['tg_webhook_path'])
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    try:
        await dp.feed_update(bot=bot, update=telegram_update)
    except TelegramBadRequest:
        pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)