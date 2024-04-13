from ds_db.db_connection import *
from ds_db.db_schemas import Base, BaseSettings
from dummy_objects import *



def test_connection():
    conn = DBConnection(port=DB_TEST_PORT, base=Base)
    assert conn.get_engine() is not None
    conn.delete_tables()
    pass


def test_setup_sqlalchemy():
    conn = DBConnection(host='sqlite:///database.db', base=BaseSettings)
    assert conn.get_engine() is not None
    conn.delete_tables()
    pass



