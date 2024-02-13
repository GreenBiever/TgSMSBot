from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from middlewares import AuthorizeMiddleware
from config import config
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

router = Router()
router.message.middleware(AuthorizeMiddleware())


@router.message(Command("start"))
async def cmd_start(msg: Message):
    START_TEXT = 'Добро пожаловать'
    await msg.answer(START_TEXT)


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


@router.message(F.text, LoginAsAdministrator.wait_password)
async def login_as_admin(msg: Message, user: User, session: AsyncSession, state: FSMContext):
    await state.set_state()
    if msg.text == config['Telegram']['admin_panel_password']:
        await msg.answer("Вы успешно вошли в админ панель")
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
