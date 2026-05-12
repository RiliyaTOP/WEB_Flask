import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from .db_session import SqlAlchemyBase


class Review(SqlAlchemyBase):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # к какому товару относится отзыв
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    # кто написал
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # оценка от 1 до 5, проверяется на уровне роута перед сохранением
    rating = Column(Integer, nullable=False)
    # текст необязателен — можно оставить только звёздочки
    text = Column(Text, nullable=True)
    created_date = Column(DateTime, default=datetime.datetime.now)
