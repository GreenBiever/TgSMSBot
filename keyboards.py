from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton



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
    #builder.row(InlineKeyboardButton(text='Рассылка📨',
    #                callback_data='mailing'))
    return builder.as_markup()


def get_main_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Арендовать номер', callback_data='buy'))
    builder.row(InlineKeyboardButton(text='Профиль👤', callback_data='profile'))
    return builder.as_markup()

def rent_number():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Россия🇷🇺', callback_data='ru'))
    return builder.as_markup()


def accept_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Купить', callback_data='accept'))
    return builder.as_markup()


def select_kb(cb_startswith: str, data: list[tuple[str, str]], page: int = 0, result_in_page: int = 8):
    if page * result_in_page >= len(data):
        raise ValueError("Very much page id or result in page")
    builder = InlineKeyboardBuilder()
    data_in_page = data[page * result_in_page: (page + 1) * result_in_page]
    btns = []
    for (key, value) in data_in_page:
        btns.append(InlineKeyboardButton(text=key, callback_data=cb_startswith + value))
        if len(btns) == 2:
            builder.row(*btns)
            btns.clear()
    builder.row(*btns)
    next_id, previous_id = page+1, page-1
    btns = []
    if previous_id >= 0:
        btns.append(InlineKeyboardButton(text='<<<<', callback_data=f'page_{previous_id}_{cb_startswith}'))
    if len(data) > result_in_page * next_id:
        btns.append(InlineKeyboardButton(text='>>>>', callback_data=f'page_{next_id}_{cb_startswith}'))
    builder.row(*btns)
    return builder.as_markup()