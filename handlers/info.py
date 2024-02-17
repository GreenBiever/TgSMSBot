from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from middlewares import AuthorizeMiddleware
from config import config
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from database.methods import change_balance
from keyboards import get_admin_panel_kb, select_kb, get_main_kb, accept_kb
from services import services, all_countries, all_services
from services.base import ServerUnavailable
import logging


all_countries = [(i,i) for i in all_countries]
all_services = [(i,i) for i in all_services]

router = Router()
router.message.middleware(AuthorizeMiddleware())
router.callback_query.middleware(AuthorizeMiddleware())

logger = logging.getLogger(__name__)

async def sms_handler(text: str, bot: Bot, tg_id: str):
    await bot.send_message(f"На номер было отправлено сообщение: <b>{text}</b>", tg_id)


@router.message(Command("start"))
async def cmd_start(msg: Message):
    START_TEXT = 'Добро пожаловать'
    await msg.answer(START_TEXT, reply_markup=get_main_kb())


@router.callback_query(F.data == 'buy')
async def rent_number(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Выберите страну", reply_markup=select_kb('countries', all_countries))
    await cb.answer()

@router.callback_query(F.data.startswith("countries"))
async def select_country(cb: CallbackQuery, state: FSMContext):
    await state.update_data({'country': cb.data[9:]})
    await cb.message.answer("Выберите сервис", reply_markup=select_kb('services', all_services))
    await cb.answer()

@router.callback_query(F.data.startswith("services"))
async def select_service(cb: CallbackQuery, state: FSMContext):
    await state.update_data({'service': cb.data[8:]})
    data = await state.get_data()
    price = None
    for service in services:
        try:
            country_id = (await service.get_countries())[data['country']]
            service_id = (await service.get_services())[data['service']]
            price = await service.get_price(country_id, service_id)
            await state.update_data({'price': price, "server": service})
        except (ServerUnavailable, ValueError):
            continue
        else:
            break
    if not price:
        logger.error("All services unavailable")
        await cb.message.answer("Произошла ошибка. Этот номер недоступен")
    else:
        await cb.message.answer(f'''Страна: {data['country']}
Сервис: {data['service']}
Стоимость аренды: <b>{price} руб</b>''', reply_markup=accept_kb())
    await cb.answer()


@router.callback_query(F.data == 'accept')
async def select_service(cb: CallbackQuery, state: FSMContext, user: User, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    try:
        service = data['server']
        country_id = (await service.get_countries())[data['country']]
        service_id = (await service.get_services())[data['service']]
        price = data['price']
    except KeyError:
        await cb.message.answer("Произошла ошибка. Выберите страну и сервис ещё раз")
        await state.clear()
        await cb.answer()
        return

    if user.balance < price:
        await cb.message.answer("На вашем счёте недостаточно средств, пополните баланс")
        await cb.answer()
        return
    try:
        telephone_number = await service.rent_number(country_id, service_id, sms_handler, bot=bot,
                                                     tg_id=cb.message.from_user.id)
    except ServerUnavailable:
        await cb.message.answer("Произошла ошибка. Попробуйте заказать номер ещё раз")
        logger.error(f"Server {service} unavailable, but method get_price not raised exception")
    else:
        await change_balance(session, user, -price)
        await cb.message.answer(f"Номер успешно арендован. Номер: <b>{telephone_number}</b>")
    finally:
        await state.set_state()
        await state.clear()
        await cb.answer()

@router.callback_query(F.data.startswith('page_'))
async def get_my_list(cb: CallbackQuery, state: FSMContext):
    _, page_id, request_id = cb.data.split('_')
    data = {'countries': all_countries, 'services': all_services}
    results = data[request_id]
    await cb.message.edit_text(text=cb.message.text, reply_markup=select_kb(request_id, results, page=int(page_id)))


@router.callback_query(F.data == 'profile')
async def get_profile(cb: CallbackQuery, user: User):
    await cb.message.answer(f'''{user}\nВаш баланс: {user.balance} руб\nTelegram ID: {user.tg_id}''')
    await cb.answer()


#####
# Login as administrator
#####

class LoginAsAdministrator(StatesGroup):
    wait_password = State()


@router.message(Command("admin", "a"))
async def enter_to_admin_panel(msg: Message, state: FSMContext, user: User):
    if not user.is_admin:
        await state.set_state(LoginAsAdministrator.wait_password)
        await msg.answer("Введите пароль: ")
    else:
        await msg.answer("Админ панель", reply_markup=get_admin_panel_kb())


@router.message(F.text, LoginAsAdministrator.wait_password)
async def login_as_admin(msg: Message, user: User, session: AsyncSession, state: FSMContext):
    await state.set_state()
    if msg.text == config['Telegram']['admin_panel_password']:
        await msg.answer("Админ панель", reply_markup=get_admin_panel_kb())
        user.is_admin = True
        session.add(user)
    else:
        await msg.answer("Пароль неверный")


@router.message(Command("exit"))
async def cmd_exit_from_admin(msg: Message, user: User, session: AsyncSession):
    if user.is_admin:
        user.is_admin = False
        session.add(user)
        await msg.answer("Вы вышли из админ панели")
