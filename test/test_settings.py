from ds_db.db_schemas import BaseSettings, LabelsOfInterest
from ds_db.db_connection import DBConnection


def init_settings_db():
    conn = DBConnection(host='sqlite:///database.db', base=BaseSettings)
    conn.delete_tables()
    conn.create_tables()
    return conn


def test_add_read_labels():
    conn = init_settings_db()
    session = conn.get_session()
    label = LabelsOfInterest()
    label.label = "hejhopp"
    session.add(label)
    session.commit()

    lbls = session.query(LabelsOfInterest).all()
    assert len(lbls) == 1
    assert lbls[0].label == "hejhopp"
