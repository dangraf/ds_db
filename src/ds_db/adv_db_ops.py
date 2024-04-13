from ds_db.db_connection import DBConnection
from ds_db.db_schemas import *
from sqlalchemy import func
from datetime import timedelta
from datetime import datetime as dt
import pandas as pd

__all__ = ['get_tracking_features']

def get_tracking_features(min_age_minutes=5):
    conn = DBConnection(base=Base)
    session = conn.get_session()
    dt_limit = dt.now() - timedelta(minutes=min_age_minutes)

    q = session.query(func.max(Frame.timestamp).label('max_time'),
                      func.max(Frame.timestamp).label('min_time'),
                      (func.max(BoundingBox.det_x_pos) - func.min(BoundingBox.det_x_pos)).label('x_delta'),
                      (func.max(BoundingBox.det_y_pos) - func.min(BoundingBox.det_y_pos)).label('y_delta'),
                      (func.max(BoundingBox.det_w) - func.min(BoundingBox.det_w)).label('w_delta'),
                      (func.max(BoundingBox.det_h) - func.min(BoundingBox.det_h)).label('h_delta'),
                      BoundingBox.tracking_id) \
        .select_from(Frame) \
        .join(BoundingBox) \
        .group_by(BoundingBox.tracking_id) \
        .where(func.max(Frame.timestamp) < dt_limit)
    df = pd.read_sql(q.statement, session.bind)
    return df
