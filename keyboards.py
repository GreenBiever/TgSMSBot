from re import I
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, KeyboardButton
from sqlalchemy.util import b



def get_admin_panel_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Статистика пользователей👤', 
                                     callback_data='user_statistic'),
                InlineKeyboardButton(text='Статистика платежей💲', 
                                     callback_data='money_statistic'))
    builder.row(InlineKeyboardButton(text='Нагрузка на сервер📈',
                                     callback_data='server_load'),
                InlineKeyboardButton(text='Баланс на сервисах для приёма смс',
                                     callback_data='balance_info'))
    builder.row(InlineKeyboardButton(text='Изменить стоимость номеров', callback_data='charge'),
                InlineKeyboardButton(text='Пополнить баланс пользователю',
                                    callback_data='top_up_user_balance'))
    builder.row(InlineKeyboardButton(text='Рассылка📨',
                    callback_data='mailing'))
    return builder.as_markup()


def get_main_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text='Арендовать номер', callback_data='buy'),
                InlineKeyboardButton(text='Профиль👤', callback_data='profile'),
                InlineKeyboardButton(text='Рефералы👥', callback_data='referral'),
                InlineKeyboardButton(text="💳Пополнить баланс", callback_data='top_up_balance'),
                InlineKeyboardButton(text='ℹ️Информация', callback_data='info'))
    builder.adjust(1, 2)
    return builder.as_markup()

def accept_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Купить', callback_data='accept'))
    return builder.as_markup()


def select_kb(cb_startswith: str, data: list[tuple[str, str]], page: int = 0, result_in_page: int = 8):
    pages_count = len(data) // result_in_page - (1 if len(data) % result_in_page == 0 else 0)
    if page > pages_count:
        raise ValueError("Very much page id or result in page")
    builder = InlineKeyboardBuilder()
    data_in_page = data[page * result_in_page: (page + 1) * result_in_page]
    for (key, value) in data_in_page:
        builder.add(InlineKeyboardButton(text=key, callback_data=cb_startswith + value))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text='Поиск🔎', callback_data=f'search_{cb_startswith}'))
    next_id, previous_id = page+1, page-1
    btns = []
    if previous_id >= 0:
        btns.append(InlineKeyboardButton(text='<<<', callback_data=f'page_0_{cb_startswith}'))
        btns.append(InlineKeyboardButton(text='<', callback_data=f'page_{previous_id}_{cb_startswith}'))
    btns.append(InlineKeyboardButton(text=f'[{page}/{pages_count}]', callback_data='pages_count'))
    if next_id <= pages_count:
        btns.append(InlineKeyboardButton(text='>', callback_data=f'page_{next_id}_{cb_startswith}'))
        btns.append(InlineKeyboardButton(text='>>>', callback_data=f'page_{pages_count}_{cb_startswith}'))
    builder.row(*btns)
    return builder.as_markup()


def referal_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Мои рефералы', callback_data='my_referals'))
    builder.row(InlineKeyboardButton(text='🔙Назад', callback_data='back'))
    return builder.as_markup()

def back_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='🔙Назад', callback_data='back'))
    return builder.as_markup()

def get_info_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Политика конфиденциальности', url='https://telegra.ph/Usloviya-i-polozheniya-predostavleniya-uslugi-SMS-Profit-09-13'))
    builder.row(InlineKeyboardButton(text='Стать поставщиком', url='https://t.me/crystal812'))
    builder.row(InlineKeyboardButton(text='🔙Назад', callback_data='back'))
    return builder.as_markup()