import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from .db_session import SqlAlchemyBase


class Employee(SqlAlchemyBase):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # один пользователь может быть только одним сотрудником
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    # должность — текстовое название, берётся из выбранной роли при регистрации
    position = Column(String, nullable=False)
    # табельный код вводится при регистрации, нужен для идентификации сотрудника
    employee_code = Column(String, nullable=False)
    hired_date = Column(DateTime, default=datetime.datetime.now)
