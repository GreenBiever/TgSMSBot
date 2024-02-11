from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from middlewares import AuthorizeMiddleware, IsAdminMiddleware
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import datetime as dt


router = Router()
router.message.middleware(AuthorizeMiddleware())
router.message.middleware(IsAdminMiddleware())


@router.message(Command("statistics"))
async def get_statistics(msg: Message, session: AsyncSession):
    yesterday = dt.datetime.now() - dt.timedelta(days=1)
    total_users = (await session.execute(select(func.count(User.id)))).first()[0]
    users_today = (await session.execute(select(func.count(User.id))
                                         .filter(User.last_login > yesterday))).first()[0]
    sign_up_today = (await session.execute(select(func.count(User.id))
                                           .filter(User.created_on > yesterday))).first()[0]
    await msg.answer(f'''<b><u>Статистика:</u></b>
Пользователей, всего: {total_users}
Сегодня зарегистрировалось: {sign_up_today}
Сегодня воспользовалось ботом: {users_today}'''
    )