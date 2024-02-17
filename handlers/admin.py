from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from middlewares import AuthorizeMiddleware, IsAdminMiddleware
from database.models import User
from database.methods import get_total_amount
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import datetime as dt
import psutil
from services import services


router = Router()
router.message.middleware(AuthorizeMiddleware())
router.callback_query.middleware(AuthorizeMiddleware())
router.message.middleware(IsAdminMiddleware())


@router.callback_query(F.data == 'user_statistic')
async def get_statistic(cb: CallbackQuery, session: AsyncSession):
    yesterday = dt.datetime.now() - dt.timedelta(days=1)
    total_users = (await session.execute(select(func.count(User.id)))).first()[0]
    users_today = (await session.execute(select(func.count(User.id))
                                         .filter(User.last_login > yesterday))).first()[0]
    sign_up_today = (await session.execute(select(func.count(User.id))
                                           .filter(User.created_on > yesterday))).first()[0]
    await cb.message.answer(f'''<b><u>Статистика:</u></b>
Пользователей, всего: {total_users}
Сегодня зарегистрировалось: {sign_up_today}
Сегодня воспользовалось ботом: {users_today}'''
    )
    await cb.answer()


@router.callback_query(F.data == 'server_load')
async def get_server_load(cb: CallbackQuery):
    await cb.answer()
    await cb.message.answer(f'''<b>Нагрузка на сервер📈</b>\nНагрузка на сервер: {psutil.cpu_percent()}%
RAM: всего {round(psutil.virtual_memory().total / 2**30)} GB, используется {psutil.virtual_memory().percent}%''')


@router.callback_query(F.data == 'balance_info')
async def get_balance_info(cb: CallbackQuery):
    msg = '<b>Баланс на сервисах для приёма смс:</b>\n'
    for service in services:
        msg += f'    {service}: {await service.get_balance()} руб\n'
    await cb.message.answer(msg)
    await cb.answer()

@router.callback_query(F.data == 'money_statistic')
async def get_money_statistic(cb: CallbackQuery, session: AsyncSession):
    total_amount, total_count = await get_total_amount(session, term=30)
    today_amount, today_count = await get_total_amount(session, term=1)
    await cb.message.answer(f'''<b>Статистика платежей:</b>
За последние 30 дней {total_count} платежей на общую сумму <b>{total_amount}</b> руб.
За сегодня {today_count} платежей на общую сумму <b>{today_amount}</b> руб.''')
    await cb.answer()
