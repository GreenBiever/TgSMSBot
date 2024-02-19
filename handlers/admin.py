import asyncio
import datetime as dt
import logging
import re

import psutil
from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from config import config
from database.connect import async_session
from database.methods import get_total_amount
from database.models import User
from middlewares import AuthorizeMiddleware, IsAdminMiddleware
from services import services
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession


router = Router()
router.message.middleware(AuthorizeMiddleware())
router.callback_query.middleware(AuthorizeMiddleware())
router.message.middleware(IsAdminMiddleware())
logger = logging.getLogger(__name__)


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
        msg += f'   • {service}: {await service.get_balance()} руб\n'
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


@router.callback_query(F.data == 'charge')
async def change_extra_charge(cb: CallbackQuery):
    await cb.message.answer(f'''<b>Изменение стоимости</b>
Текущая стоимость номера: {float(config['Telegram']['amount']) * 100}% от его первоначальной стоимости.
Чтобы изменить стоимость, используйте следующие команды:
/up 30 - увеличить стоимость на 30%
/down 40 - уменьшить стоимость на 40%
    ''')
    await cb.answer()

@router.message(Command("up"))
async def up_charge(msg: Message, command: CommandObject):
    try:
        new_amount = float(config['Telegram']['amount']) + (int(command.args) / 100)
    except ValueError:
        await msg.answer("Введённые данные некорректны.Укажите только число, без знака % ")
    else:
        config['Telegram']['amount'] = str(new_amount)
        await msg.answer("Стоимость изменена")

@router.message(Command("down"))
async def down_charge(msg: Message, command: CommandObject):
    try:
        new_amount = float(config['Telegram']['amount']) - (int(command.args) / 100)
        if new_amount < 0:
            await msg.answer("Стоимость не может быть меньше 0%")
            return
    except ValueError:
        await msg.answer("Введённые данные некорректны.Укажите только число, без знака % ")
    else:
        config['Telegram']['amount'] = str(new_amount)
        await msg.answer("Стоимость изменена")

class TopUpUserBalance(StatesGroup):
    wait_username = State()
    wait_value = State()


@router.callback_query(F.data == 'top_up_user_balance')
async def top_up_user_balance(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Введите ID пользователя или его @username")
    await cb.answer()
    await state.set_state(TopUpUserBalance.wait_username)

@router.message(F.text, TopUpUserBalance.wait_username)
async def set_username(msg: Message, state: FSMContext, session: AsyncSession):
    if msg.text.isdigit():
        user = (await session.execute(select(User).where(User.tg_id == msg.text))).scalar()
    else:
        user = (await session.execute(select(User).where(User.username == msg.text.strip("@")))).scalar()
    if not user:
        await msg.answer("Пользователь не найден")
        await state.set_state()
    else:
        await state.update_data({'username': msg.text, 'user_id': user.id})
        await msg.answer("Введите сумму")
        await state.set_state(TopUpUserBalance.wait_value)

@router.message(F.text, TopUpUserBalance.wait_value)
async def set_value(msg: Message, state: FSMContext, session: AsyncSession):
    try:
        value = float(msg.text)
    except ValueError:
        await msg.answer("Введённые данные некорректны.Укажите только число")
    else:
        data = await state.get_data()
        await session.execute(update(User).where(User.id == data['user_id']).values(balance=User.balance + value))
        await msg.answer("Сумма пополнена")
        await state.set_state()
        await state.clear()


class SetMailing(StatesGroup):
    wait_msg = State()
    wait_interval = State()

@router.callback_query(F.data == 'mailing')
async def create_mailing(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Отправьте сообщение, которое будет отправляться пользователям(чтобы\
отменить создание новой рассылки, введите /cancel)")
    await cb.answer()
    await state.set_state(SetMailing.wait_msg)

@router.message(StateFilter(SetMailing), Command("cancel"))
async def cancle_mailing(msg: Message, state: FSMContext):
    await msg.answer("Рассылка отменена")
    await state.clear()

@router.message(F, SetMailing.wait_msg)
async def set_msg_text(msg: Message, state: FSMContext):
    await state.update_data({'message': msg})
    await msg.answer("Введите время(в формате: 1m 1h 1d), через которое будет отправлена рассылка(или '0', чтобы отправить сейчас)")
    await state.set_state(SetMailing.wait_interval)

def parse_date(text: str):
    duration = dt.timedelta()
    pattern = '\d+[dmh]'
    for match in re.findall(pattern, text):
        if match[-1] == 'd':
            duration += dt.timedelta(days=int(match[:-1]))
        elif match[-1] == 'h':
            duration += dt.timedelta(hours=int(match[:-1]))
        elif match[-1] == 'm':
            duration += dt.timedelta(minutes=int(match[:-1]))
    return duration

async def mail(message: Message, bot: Bot, delay: dt.timedelta):
    await asyncio.sleep(delay.seconds)
    logger.info("Mailing")
    async with async_session() as session:
        tg_ids = (await session.execute(select(User.tg_id))).scalars().all()
    await asyncio.gather(*[bot.copy_message(tg_id, message.chat.id, message.message_id) for tg_id in tg_ids])

@router.message(F.text, SetMailing.wait_interval)
async def set_interval(msg: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    asyncio.create_task(mail(message=data['message'], bot=bot,
                                          delay=parse_date(msg.text)))
    await state.clear()
    await msg.answer("Рассылка успешно создана")