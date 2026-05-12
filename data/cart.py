from sqlalchemy import Column, Integer, ForeignKey
from .db_session import SqlAlchemyBase


class Cart(SqlAlchemyBase):
    __tablename__ = 'cart_products'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # привязываем запись к конкретному пользователю
    user_id = Column(Integer, ForeignKey('users.id'))
    # и к конкретному товару
    product_id = Column(Integer, ForeignKey('products.id'))

    # сколько единиц этого товара лежит в корзине
    quantity = Column(Integer, default=1)
