from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Payment
import datetime as dt


async def change_balance(session: AsyncSession, user: User, amount: int) -> int:
    '''Change user balance in DB
    :param amount: Amount that added to user balance. May be negative and positive
    :return: actual user balance'''
    await session.execute(update(User).where(User.id == user.id).values(balance=user.balance + amount))
    payment = Payment(user=user, amount=amount)
    session.add_all([user, payment])
    return user.balance + amount


async def get_total_amount(session: AsyncSession, term: int = 1) -> tuple[int, int]:
    '''Get total amount of payments in DB
    :return: (total payments amount, payments count)'''
    query = (select(func.sum(Payment.amount))
                .where((Payment.created_on > dt.datetime.now() - dt.timedelta(days=term)) & (Payment.amount > 0)))
    query2 = (select(func.count(Payment.amount))
                .where((Payment.created_on > dt.datetime.now() - dt.timedelta(days=term)) & (Payment.amount > 0)))
    
    return [(await session.execute(q)).scalars().first() or 0 for q in (query, query2)]