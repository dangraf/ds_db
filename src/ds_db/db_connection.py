from sqlalchemy import create_engine, Insert, func, Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import Session
from ds_db.db_schemas import Base, BaseSettings
from typing import Dict

engines: Dict = {}
__all__ = ['DBConnection',
           'flatten_array']


class DBConnection:

    def __init__(self, host: str = 'localhost',
                 port: int = 5432,
                 password: str = 'hellohellomydear',
                 user: str = 'docker',
                 db: str = 'deepdb',
                 base=Base):
        self.host = host
        self.port = port
        self.password = password
        self.user = user
        self.db = db
        self.base = base

        self.set_engine()

    def get_engine(self):
        global engines
        return engines.get(self.base, None)

    def get_session(self):
        global engines
        return Session(engines.get(self.base, None))

    def create_tables(self):
        global engines
        self.base.metadata.create_all(engines.get(self.base, None), checkfirst=True)

    def set_engine(self):
        global engines
        database = {'host': self.host,
                    'port': self.port,
                    'password': self.password,
                    'username': self.user,
                    'database': self.db,
                    'drivername': 'postgresql+psycopg2'}
        engine = engines.get(self.base, None)
        if engine is None:
            if "sqlite:" in database['host']:
                print(database['host'])
                engines[self.base] = create_engine(database['host'], echo=True)
            else:
                engines[self.base] = create_engine(URL.create(**database))
            engines[self.base].connect()

        self.create_tables()

    def delete_tables(self):
        global engines
        self.base.metadata.drop_all(engines.get(self.base, None), checkfirst=False)


def flatten_array(array):
    return [a[0] for a in array]
