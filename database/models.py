from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import Integer, VARCHAR, Column, DateTime, ForeignKey, Boolean, Float, Table
from datetime import datetime


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    tg_id = Column(VARCHAR(10), unique=True, nullable=False)
    fname = Column(VARCHAR(100))
    lname = Column(VARCHAR(100))
    username = Column(VARCHAR(100))
    last_login = Column(DateTime(), default=datetime.now)
    created_on = Column(DateTime(), default=datetime.now)
    is_blocked = Column(Boolean, default=False)
    balance = Column(Integer, nullable=False, default=0)

    def __str__(self):
        return f"{self.fname} {self.lname}"

    def __repr__(self):
        return f"<{self.id}>: {self.fname} {self.lname}"


class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('User', backref='payments')
    amount = Column(Integer, nullable=False)
    created_on = Column(DateTime(), default=datetime.now)

    def __repr__(self):
        return f"payment<{self.id}> to user {self.user}, amount: {self.amount}"

class TelephoneNumber(Base):
    __tablename__ = 'telephone_numbers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(VARCHAR(16), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', backref='telephone_numbers')

    def __str__(self):
        return self.number
