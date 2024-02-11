import asyncio
from aiogram import Bot, Dispatcher
from config import config
from handlers import info, admin
from database.connect import init_models
import logging





async def main():
    logging.basicConfig(level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    bot = Bot(config['App']['bot_token'], parse_mode='HTML')
    dp = Dispatcher()
    await init_models()
    dp.include_routers(info.router, admin.router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())