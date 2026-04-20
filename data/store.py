from sqlalchemy import Column, Integer, String, Float
from .db_session import SqlAlchemyBase


class Store(SqlAlchemyBase):
    __tablename__ = 'stores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
