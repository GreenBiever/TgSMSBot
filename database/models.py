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

    def __str__(self):
        return f"{self.fname} {self.lname}"

    def __repr__(self):
        return f"<{self.id}>: {self.fname} {self.lname}"