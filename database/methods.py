from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Payment


async def change_ballance(session: AsyncSession, user: User, amount: int) -> int:
    '''Change user balance in DB
    :param amount: Amount that added to user balance. May be negative and positive
    :return: actual user balance'''
    await session.execute(update(User).where(User.id == user.id).values(balance=user.balance + amount))
    payment = Payment(user=user, amount=amount)
    session.add_all([user, payment])
    return user.balance + amount