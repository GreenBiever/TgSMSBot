from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.deep_linking import create_start_link
from middlewares import AuthorizeMiddleware
from config import config
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from database.methods import change_balance, get_amount, get_expenses, get_number_of_activations
from keyboards import (get_admin_panel_kb, select_kb, get_main_kb,
                      accept_kb, referal_menu_kb, back_kb, get_info_kb, select_lang_kb)
from services import services, all_countries, all_services
from services.base import ServerUnavailable
import logging
import pycountry
from lang_pkg.translate import parse_lang_data, CountriesEnum



def get_flag(country: str) -> str:
    country = pycountry.countries.get(name=country)
    if country is not None:
        return country.flag
    return ''


all_countries = [(f"{get_flag(i)} {i}",i) for i in all_countries]
all_services = [(i,i) for i in all_services]

router = Router()
router.message.middleware(AuthorizeMiddleware())
router.callback_query.middleware(AuthorizeMiddleware())

logger = logging.getLogger(__name__)

async def sms_handler(text: str, bot: Bot, tg_id: str, user: User):
    await bot.send_message(user.translate("new_sms", text=text), tg_id)


@router.message(Command("start"))
async def cmd_start(msg: Message, user: User):
    await msg.answer(user.translate('start_text'),
                    reply_markup=get_main_kb(user))


@router.callback_query(F.data == 'buy')
async def rent_number(cb: CallbackQuery, user: User):
    await cb.message.answer(user.translate("select_service"), reply_markup=select_kb('services', all_services, user))
    await cb.answer()

@router.callback_query(F.data.startswith("services"))
async def select_country(cb: CallbackQuery, state: FSMContext, user: User):
    await state.update_data({'service': cb.data[8:]})
    await cb.message.answer(user.translate("select_service"), reply_markup=select_kb('countries', all_countries. user))
    await cb.answer()

@router.callback_query(F.data.startswith("countries"))
async def select_service(cb: CallbackQuery, state: FSMContext, user: User):
    await state.update_data({'country': cb.data[9:]})
    data = await state.get_data()
    if 'service' not in data:
        await cb.message.answer(user.translate("select_service_after_country"))
        await cb.answer()
        return
    price = None
    for service in services:
        try:
            country_id = (await service.get_countries())[data['country']]
            service_id = (await service.get_services())[data['service']]
            price = (await service.get_price(country_id, service_id)) * float(config['Telegram']['amount'])
            await state.update_data({'price': price, "server": service})
        except (ServerUnavailable, KeyError):
            continue
        else:
            break
    if not price:
        logger.error("All services unavailable")
        await cb.message.answer(user.translate("number_not_available"))
    else:
        await cb.message.answer(user.translate("rent_detail", country=data['country'],service=data['service'],
                                              price=price), reply_markup=accept_kb())
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
        await cb.message.answer(user.translate("error"))
        await state.clear()
        await cb.answer()
        return

    if user.balance < price:
        await cb.message.answer(user.translate("low_balance"))
        await cb.answer()
        return
    try:
        telephone_number = await service.rent_number(country_id, service_id, sms_handler, bot=bot,
                                                     tg_id=cb.message.from_user.id)
    except ServerUnavailable:
        await cb.message.answer(user.translate("error"))
        logger.error(f"Server {service} unavailable, but method get_price not raised exception")
    else:
        await change_balance(session, user, -price)
        await cb.message.answer(user.translate("rented",telephone_number=telephone_number))
    finally:
        await state.clear()
        await cb.answer()

@router.callback_query(F.data.startswith('page_'))
async def get_my_list(cb: CallbackQuery, state: FSMContext, user: User):
    _, page_id, request_id = cb.data.split('_')
    data = {'countries': all_countries, 'services': all_services}
    results = data[request_id]
    await cb.message.edit_text(text=cb.message.text, reply_markup=select_kb(request_id, results, page=int(page_id), user=user))


@router.callback_query(F.data == 'profile')
async def get_profile(cb: CallbackQuery, user: User, session: AsyncSession):
    total_amount = await get_amount(session, user.id)
    total_expenses = await get_expenses(session, user.id)
    number_of_rent = await get_number_of_activations(session, user.id)
    await cb.message.edit_text(user.translate("profile",name=str(user), tg_id=user.tg_id, balance=user.balance, total_amount=total_amount, 
                                              total_expenses=total_expenses, number_of_rent=number_of_rent),
                              reply_markup=back_kb(user))

class SearchStates(StatesGroup):
    wait_text = State()

@router.callback_query(F.data.startswith('search_'))
async def start_search_number(cb: CallbackQuery, state: FSMContext, user):
    section = cb.data.split('_')[1]
    await state.update_data({'section': section})
    await cb.message.answer(user.transalte("wait_search_text"))
    await state.set_state(SearchStates.wait_text)
    await cb.answer()


@router.message(F.text, SearchStates.wait_text)
async def search_number(msg: Message, state: FSMContext, user: User):
    state_data = await state.get_data()
    data = all_countries if state_data['section'] == 'countries' else all_services
    result = []
    for i in data:
        if msg.text in i[0]:
            result.append(i)
    if result:
        await msg.answer(user.translate("found_result"), reply_markup=select_kb(
            state_data['section'], result, user))
    else:
        await msg.answer(user.translate("not_found"))

@router.callback_query(F.data == 'referral')
async def referal_info(cb: CallbackQuery, bot: Bot, user: User):
    link = await create_start_link(bot, user.id, encode=True)
    await cb.message.edit_text(user.translate('referal_menu', ref_link=link), reply_markup=referal_menu_kb(user))

@router.callback_query(F.data == 'back')
async def go_to_main_menu(cb: CallbackQuery, user: User):
    await cb.message.edit_text(user.translate('start_text'), reply_markup=get_main_kb(user))

@router.callback_query(F.data == 'my_referals')
async def get_my_referals(cb: CallbackQuery, session: AsyncSession, user: User):
    user = (await session.execute(select(User).where(User.id == user.id)  # The same one user,
                .options(selectinload(User.referers)))).scalars().first() # but with selectinload to user.referers
    number_of_referals = len(user.referers)
    await cb.answer()
    msg = ''
    if number_of_referals:
        for number, referal in zip(range(1,number_of_referals+1), user.referers):
            msg += f"\n{number}) {referal}"
    await cb.message.answer(user.translate("my_referal", number_of_referals=number_of_referals,
                                           your_referals=msg or "0"), parse_mode='markdown')

@router.callback_query(F.data == 'info')
async def get_info(cb: CallbackQuery, user: User):
    await cb.message.edit_text(user.translate("btn_info"), reply_markup=get_info_kb())


@router.callback_query(F.data == 'change_lang')
async def change_lang(cb: CallbackQuery, user: User, session: AsyncSession):
    languages = [lang.name for lang in CountriesEnum if user.language != lang]
    await cb.message.edit_text(user.translate("select_lang"), reply_markup=select_lang_kb(user, languages))

@router.callback_query(F.data.startswith('set_lang_'))
async def set_lang(cb: CallbackQuery, user: User, session: AsyncSession):
    user.language = getattr(CountriesEnum, cb.data.split('_')[2])
    session.add(user)
    await cb.message.edit_text(user.translate('start_text'), reply_markup=get_main_kb(user))

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
