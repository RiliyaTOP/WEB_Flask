import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

# базовый класс для всех моделей — от него наследуются все таблицы
SqlAlchemyBase = orm.declarative_base()

# фабрика сессий хранится здесь, чтобы создавать её только один раз при старте
__factory = None

def global_init(db_file):
    # не переинициализируем если уже запускались — защита от двойного вызова
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("database.db")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")

    # echo=False чтобы SQLAlchemy не спамил SQL-запросами в консоль
    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    # импортируем все модели здесь, иначе SQLAlchemy не знает о таблицах
    # и metadata.create_all ничего не создаст
    from . import __all_models

    # создаём таблицы которых ещё нет, уже существующие не трогает
    SqlAlchemyBase.metadata.create_all(engine)

def create_session() -> Session:
    # каждый раз возвращает новую сессию — не переиспользуем одну на весь запрос
    global __factory
    return __factory()
