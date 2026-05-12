from sqlalchemy import Column, Integer, ForeignKey, DateTime
import datetime
from .db_session import SqlAlchemyBase


class Wishlist(SqlAlchemyBase):
    __tablename__ = 'wishlist'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # кто добавил в избранное
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # что добавил в избранное
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    # когда добавил — пригодится если захотим сортировать избранное по дате
    created_date = Column(DateTime, default=datetime.datetime.now)
