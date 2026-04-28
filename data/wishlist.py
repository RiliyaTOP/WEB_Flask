from sqlalchemy import Column, Integer, ForeignKey, DateTime
import datetime
from .db_session import SqlAlchemyBase


class Wishlist(SqlAlchemyBase):
    __tablename__ = 'wishlist'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.now)
