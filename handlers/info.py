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
                       accept_kb, referal_menu_kb, back_kb, get_info_kb, get_payment_methods_kb,
                       get_crypto_bot_currencies_kb, check_crypto_bot_kb)
from services import services, all_countries, all_services
from services.base import ServerUnavailable
import logging
import pycountry
from aiocryptopay import AioCryptoPay


def get_flag(country: str) -> str:
    country = pycountry.countries.get(name=country)
    if country is not None:
        return country.flag
    return ''


all_countries = [(f"{get_flag(i)} {i}", i) for i in all_countries]
all_services = [(i, i) for i in all_services]

router = Router()
router.message.middleware(AuthorizeMiddleware())
router.callback_query.middleware(AuthorizeMiddleware())

logger = logging.getLogger(__name__)

START_TEXT = 'Добро пожаловать'


async def sms_handler(text: str, bot: Bot, tg_id: str):
    await bot.send_message(f"На номер было отправлено сообщение: <b>{text}</b>", tg_id)


@router.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer(START_TEXT, reply_markup=get_main_kb())


@router.callback_query(F.data == 'buy')
async def rent_number(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Выберите сервис", reply_markup=select_kb('services', all_services))
    await cb.answer()


@router.callback_query(F.data.startswith("services"))
async def select_country(cb: CallbackQuery, state: FSMContext):
    await state.update_data({'service': cb.data[8:]})
    await cb.message.answer("Выберите страну", reply_markup=select_kb('countries', all_countries))
    await cb.answer()


@router.callback_query(F.data.startswith("countries"))
async def select_service(cb: CallbackQuery, state: FSMContext):
    await state.update_data({'country': cb.data[9:]})
    data = await state.get_data()
    if 'service' not in data:
        await cb.message.answer("Прежде чем выбирать страну, выберите сервис, для которого вы заказываете номер")
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
        await state.clear()
        await cb.answer()


@router.callback_query(F.data.startswith('page_'))
async def get_my_list(cb: CallbackQuery, state: FSMContext):
    _, page_id, request_id = cb.data.split('_')
    data = {'countries': all_countries, 'services': all_services}
    results = data[request_id]
    await cb.message.edit_text(text=cb.message.text, reply_markup=select_kb(request_id, results, page=int(page_id)))


@router.callback_query(F.data == 'profile')
async def get_profile(cb: CallbackQuery, user: User, session: AsyncSession):
    total_amount = await get_amount(session, user.id)
    total_expenses = await get_expenses(session, user.id)
    number_of_rent = await get_number_of_activations(session, user.id)
    await cb.message.edit_text(f'''{user}\n
Ваш ID: {user.tg_id}
💰 Ваш баланс: {user.balance} руб.

📥 Пополнений на сумму: {total_amount} руб.
🛒 Активаций на сумму: {total_expenses} руб.
📲 Всего номеров арендовано: {number_of_rent}''', reply_markup=back_kb())


@router.callback_query(F.data == 'pages_count')
async def print_pages_count(cb: CallbackQuery):
    await cb.answer("Не кнопка")


class SearchStates(StatesGroup):
    wait_text = State()


@router.callback_query(F.data.startswith('search_'))
async def start_search_number(cb: CallbackQuery, state: FSMContext):
    section = cb.data.split('_')[1]
    await state.update_data({'section': section})
    await cb.message.answer('Введите название: ')
    await state.set_state(SearchStates.wait_text)
    await cb.answer()


@router.message(F.text, SearchStates.wait_text)
async def search_number(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    data = all_countries if state_data['section'] == 'countries' else all_services
    result = []
    for i in data:
        if msg.text in i[0]:
            result.append(i)
    if result:
        await msg.answer("Найденные варианты:", reply_markup=select_kb(
            state_data['section'], result))
    else:
        await msg.answer("По вашему запросу ничего не найдено")


@router.callback_query(F.data == 'referral')
async def referal_info(cb: CallbackQuery, bot: Bot, user: User):
    link = await create_start_link(bot, user.id, encode=True)
    await cb.message.edit_text(f'''👥 Реферальная система

▫️ Ваша реферальная ссылка:

{link}

❗️Если человек, приглашенный по вашей реферальной ссылке, пополнит баланс, \
то вы получите 5% от суммы его депозита.''', reply_markup=referal_menu_kb())


@router.callback_query(F.data == 'back')
async def go_to_main_menu(cb: CallbackQuery):
    await cb.message.edit_text(START_TEXT, reply_markup=get_main_kb())


@router.callback_query(F.data == 'my_referals')
async def get_my_referals(cb: CallbackQuery, session: AsyncSession, user: User):
    user = (await session.execute(select(User).where(User.id == user.id)  # The same one user,
                                  .options(
        selectinload(User.referers)))).scalars().first()  # but with selectinload to user.referers
    number_of_referals = len(user.referers)
    await cb.answer()
    msg = f'По вашей ссылке зарегистрировалось пользователей: <b>{number_of_referals}</b>'
    if number_of_referals:
        msg += "<b>Ваши рефералы:</b>:"
        for number, referal in zip(range(1, number_of_referals + 1), user.referers):
            msg += f"\n{number}) {referal}"
    await cb.message.answer(msg)


@router.callback_query(F.data == 'info')
async def get_info(cb: CallbackQuery):
    await cb.message.edit_text("ℹ️<b>Информация</b>", reply_markup=get_info_kb())


class TopUpBalance(StatesGroup):
    amount = State()
    invoice_id = State()


@router.callback_query(F.data == 'top_up_balance')
async def get_top_up_methods(cb: CallbackQuery, session: AsyncSession, user: User):
    await cb.message.edit_text("Выберите способ пополнения баланса", reply_markup=get_payment_methods_kb())


@router.callback_query(F.data == "payment_cryptobot")
async def crypto_bot_step1(cb: CallbackQuery, state: FSMContext):
    crypto_bot_link = "https://t.me/CryptoBot"
    message_text = (
        f'<b><a href="{crypto_bot_link}">⚜️ CryptoBot</a></b>\n\n'
        '— Минимум: <b>0.1 $</b>\n\n'
        '<b>💸 Введите сумму пополнения в долларах</b>'
    )
    await cb.message.edit_text(message_text, disable_web_page_preview=True)
    await state.set_state(TopUpBalance.amount)
    await cb.answer()


@router.message(F.text, TopUpBalance.amount)
async def crypto_bot_step2(msg: Message, state: TopUpBalance.amount):
    state_data = await state.get_data()
    amount = msg
    try:
        if float(amount.text) >= 0.1:
            crypto_bot_link = "https://t.me/CryptoBot"
            message_text = (
                f'<b><a href="{crypto_bot_link}">⚜️ CryptoBot</a></b>\n\n'
                f'— Сумма: <b>{amount.text} $</b>\n\n'
                '<b>💸 Выберите валюту, которой хотите оплатить счёт</b>'
            )
            await msg.answer(text=message_text, parse_mode='HTML', disable_web_page_preview=True,
                             reply_markup=get_crypto_bot_currencies_kb())
            await state.update_data(amount=float(msg.text))
        else:
            await msg.answer(
                '<b>⚠️ Минимум: 0.1 $!<b>'
            )
    except ValueError:
        await msg.answer(
            '<b>❗️Сумма для пополнения должна быть в числовом формате!</b>'
        )


@router.callback_query(F.data.startswith('crypto_bot_currency|'))
async def crypto_bot_step3(cb: CallbackQuery, state: TopUpBalance.amount):
    try:
        cryptopay = AioCryptoPay(config['payment_api_keys']['CRYPTO_BOT'])
        print(cryptopay)
        asset = cb.data.split('|')[1].upper()
        payment_data = await state.get_data()
        amount = payment_data.get('amount')
        invoice = await cryptopay.create_invoice(
            asset=asset,
            amount=amount
        )
        await cryptopay.close()
        invoice_id_state = invoice.invoice_id
        await state.update_data(invoice_id=invoice_id_state)
        await cb.message.edit_text(f'<b>💸 Отправьте {amount} $ <a href="{invoice.bot_invoice_url}">по ссылке</a></b>',
                                   reply_markup=check_crypto_bot_kb(invoice.bot_invoice_url, invoice.invoice_id))
    except Exception as e:
        await cb.message.edit_text(
            f'<b>⚠️ Произошла ошибка! {e}</b>'
        )


@router.callback_query(F.data.startswith("check_crypto_bot"))
async def crypto_bot_step4(cb: CallbackQuery, state: TopUpBalance.amount, session: AsyncSession, user: User):
    payment_data = await state.get_data()
    invoice_id = payment_data.get("invoice_id")
    amount = payment_data.get("amount")
    amount_db = int(amount) * 90
    cryptopay = AioCryptoPay(config['payment_api_keys']['CRYPTO_BOT'])
    invoice = await cryptopay.get_invoices(invoice_ids=invoice_id)
    await cryptopay.close()
    if invoice and invoice.status == 'paid':
        await cb.answer('✅ Оплата прошла успешно!',
                        show_alert=True)
        await change_balance(session, user, amount_db)
        await cb.message.answer(f'<b>💸 Ваш баланс пополнен на сумму {amount} $!</b>', parse_mode='HTML')
    else:
        await cb.answer('❗️ Вы не оплатили счёт!',
                        show_alert=True)


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
