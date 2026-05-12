import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class ProductImage(SqlAlchemyBase):
    __tablename__ = 'product_images'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # к какому товару привязана картинка
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    # только имя файла, полный путь строится динамически через url_for в шаблонах
    filename = Column(String, nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.now)
