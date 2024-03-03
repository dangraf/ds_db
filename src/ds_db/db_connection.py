from sqlalchemy import create_engine, Insert, func, Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import Session
from ds_db.db_schemas import Base

engine: Engine = None

__all__ = ['DBConnection',
           'flatten_array']


class DBConnection:

    def __init__(self, host: str = 'localhost',
                 port: int = 5432,
                 password: str = 'hellohellomydear',
                 user: str = 'docker',
                 db: str = 'deepdb'):
        self.host = host
        self.port = port
        self.password = password
        self.user = user
        self.db = db
        self.set_engine()

    def get_engine(self):
        global engine
        return engine

    def get_session(self):
        global engine
        return Session(engine)

    def create_tables(self):
        global engine
        Base.metadata.create_all(engine, checkfirst=True)

    def set_engine(self):
        global engine
        database = {'host': self.host,
                    'port': self.port,
                    'password': self.password,
                    'username': self.user,
                    'database': self.db,
                    'drivername': 'postgresql+psycopg2'}
        if engine is None:
            if "sqlite:" in database['host']:
                print(database['host'])
                engine = create_engine(database['host'], echo=True)
            else:
                engine = create_engine(URL.create(**database))
            engine.connect()

        self.create_tables()

    def delete_tables(self):
        global engine
        Base.metadata.drop_all(engine, checkfirst=False)


def flatten_array(array):
    return [a[0] for a in array]
