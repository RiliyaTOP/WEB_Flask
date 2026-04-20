import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from .db_session import SqlAlchemyBase


class Employee(SqlAlchemyBase):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    position = Column(String, nullable=False)
    employee_code = Column(String, nullable=False)
    hired_date = Column(DateTime, default=datetime.datetime.now)
