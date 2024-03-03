from ds_db.db_schemas import *
from ds_db.path_operators import *
from datetime import datetime

from dummy_objects import *


def test_save_file_to_db():
    f = File()
    f.stream_nbr = 0
    f.filepath = '/hej/blabla.txt'
    f.num_frames = 503
    f.start_date = datetime.now()
    f.end_date = datetime.now()
    f.frame_offset = 10

    conn = init_connection()
    session = conn.get_session()
    session.add(f)
    session.commit()
    cnt = session.query(File).count()
    assert cnt == 1
    session.close()


def test_save_frame_to_db_no_file_ref():
    f = get_random_frame()

    conn = init_connection()
    session = conn.get_session()

    session.add(f)
    session.commit()
    cnt = session.query(Frame).count()
    assert cnt == 1
    session.close()


def test_save_frames_with_detections():
    conn = init_connection()
    session = conn.get_session()

    f = get_random_frame()
    for i in range(3):
        o = get_random_bboxobject()
        f.objects.append(o)
    session.add(f)
    session.commit()

    assert session.query(Frame).count() == 1
    assert session.query(BoundingBox).count() == 3
    session.close()


def test_framemeta_to_object():
    frame_meta = DummyFrameMeta()
    f = Frame()
    f.frame_meta2frame(frame_meta)
    assert f.frame_number == frame_meta.frame_num
    assert f.source_id == frame_meta.source_id
    assert type(f.timestamp) is datetime

    conn = init_connection()

    session = conn.get_session()
    session.add(f)
    session.commit()
    session.close()


def test_metadata_to_object():
    frame_meta = DummyFrameMeta()
    f = Frame()
    f.frame_meta2frame(frame_meta)

    obj_meta = DummyObjMeta()
    b = BoundingBox()
    b.obj_meta2bbox(obj_meta)

    assert b.confidence == obj_meta.confidence
    assert b.label == obj_meta.obj_label

    conn = init_connection()

    f.objects.append(b)

    session = conn.get_session()
    session.add(f)
    session.commit()
    session.close()


def test_file_table():
    f = File()
    video_path = get_relative_path_from_file(__file__, 'resources/out_stream0_2024-02-16T09_40_34_0000.mp4')
    f.update_from_filepath(video_path)
    assert f.filepath == str(video_path)
    assert f.stream_nbr == 0
    assert f.num_frames == 286
    # 10 second video
    assert f.end_date == datetime(year=2024, month=2, day=16, hour=10, minute=40, second=45, microsecond=517137)
    assert f.start_date == datetime(year=2024, month=2, day=16, hour=10, minute=40, second=35, microsecond=983804)
    assert f.frame_offset == 0