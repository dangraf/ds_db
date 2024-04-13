from ds_db.db_connection import DBConnection
from pathlib import Path

__all__ = ['get_dummy_file',
           'get_random_frame',
           'get_random_bboxobject',
           'BboxCoords',
           'BboxInfo',
           'DummyObjMeta',
           'DummyFrameMeta',
           'init_connection',
           'DB_TEST_PORT']

from ds_db.db_schemas import Frame, BoundingBox, File
from datetime import datetime

DB_TEST_PORT = 5433


def get_dummy_file():
    f = File()
    f.stream_nbr = 0
    f.filepath = '/hej/blabla.txt'
    f.num_frames = 503
    f.start_date = datetime.now()
    f.end_date = datetime.now()
    f.frame_offset = 10
    return f

def get_random_frame(frame_number=10, source_id=0):
    f = Frame()
    f.frame_number = frame_number
    f.source_id = source_id
    f.timestamp = datetime.now()
    return f


def get_random_bboxobject(tracking_id=10):
    b = BoundingBox()
    b.label = 'car'
    b.tracking_id = tracking_id
    b.bbox = [1, 2, 3, 4]
    b.tbox = [5, 6, 7, 8]
    b.confidence = 0.7
    b.track_conf = 0.1
    return b


class BboxCoords:
    def __init__(self, left: int, top: int, width: int, height: int):
        self.left = left
        self.top = top
        self.width = width
        self.height = height


class BboxInfo:
    def __init__(self, left, top, width, height):
        self.org_bbox_coords = BboxCoords(left, top, width, height)


class DummyObjMeta:
    def __init__(self):
        self.obj_label = "car"
        self.confidence = 0.7
        self.object_id = 10
        self.tracker_confidence = 0.3
        self.detector_bbox_info = BboxInfo(10, 20, 30, 40)
        self.tracker_bbox_info = BboxInfo(50, 60, 70, 80)


class DummyFrameMeta:
    def __init__(self, source_id=0, frame_num=1):
        self.source_id = source_id
        self.frame_num = frame_num
        now = datetime.now()
        ts = datetime.timestamp(now)
        self.ntp_timestamp = int(ts * 1000000000)


def init_connection():
    conn = DBConnection(port=5433)
    conn.delete_tables()
    conn.create_tables()
    return conn
