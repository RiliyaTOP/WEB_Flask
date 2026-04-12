import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, create_engine
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    email = Column(String, index=True, unique=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    role = Column(Enum("admin", "user", "manager", "warehouse", "support", "courier", name="user_roles"), nullable=True)
    created_date = Column(DateTime, default=datetime.datetime.now)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    role = Column(Enum("admin", "user", "manager", "warehouse", "support", "courier", name="user_roles"), nullable=True)
    created_date = Column(DateTime, default=datetime.datetime.now)