import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, create_engine
from .db_session import SqlAlchemyBase


class Products(SqlAlchemyBase, UserMixin):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True, unique=True)
    price = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=True)
    created_date = Column(DateTime, default=datetime.datetime.now)