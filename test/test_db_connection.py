from ds_db.db_connection import *
from dummy_objects import *


def test_connection():
    conn = DBConnection(port=DB_TEST_PORT)
    assert conn.get_engine() is not None
    conn.delete_tables()
    pass


def test_setup_sqlalchemy():
    conn = DBConnection(host='sqlite:///database.db')
    assert conn.get_engine() is not None
    conn.delete_tables()
    pass



