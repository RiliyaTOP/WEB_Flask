import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, create_engine
from .db_session import SqlAlchemyBase


class Products(SqlAlchemyBase, UserMixin):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # unique=True — два товара с одинаковым названием добавить не получится
    name = Column(String, nullable=True, unique=True)
    price = Column(Integer, nullable=True)
    # количество показывает остаток на складе
    quantity = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    # категория используется для фильтрации в каталоге
    category = Column(String, nullable=True)
    created_date = Column(DateTime, default=datetime.datetime.now)
