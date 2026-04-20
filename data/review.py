import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from .db_session import SqlAlchemyBase


class Review(SqlAlchemyBase):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rating = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    created_date = Column(DateTime, default=datetime.datetime.now)
