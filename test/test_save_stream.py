import time
from pathlib import Path
from datetime import datetime
from ds_db.all import *
from dummy_objects import *
from sqlalchemy import select


def test_get_offset():
    conn = init_connection()

    ssaver = StreamSaver()
    offset = ssaver.get_track_id_offset()
    assert offset == 0
    assert ssaver.trackid_offset == 0

    frame = get_random_frame()
    bbox = get_random_bboxobject(tracking_id=10)
    session = conn.get_session()
    frame.objects.append(bbox)
    session.add(frame)
    session.commit()

    offset = ssaver.get_track_id_offset()
    assert offset == 11
    assert ssaver.trackid_offset == 0
    session.close()
    ssaver.close()


def test_save_frame_meta():
    conn = init_connection()
    frame_meta = DummyFrameMeta()
    f = Frame()
    f.frame_meta2frame(frame_meta)

    with conn.get_session() as session:
        session.add(f)
        session.commit()


def test_save_frame_meta_and_obj_meta():
    conn = init_connection()
    frame_meta = DummyFrameMeta()
    f = Frame()
    f.frame_meta2frame(frame_meta)

    obj_meta = DummyObjMeta()
    bbox = BoundingBox()
    bbox.obj_meta2bbox(obj_meta)
    f.objects.append(bbox)

    with conn.get_session() as session:
        session.add(f)
        session.commit()


def test_run_thread():
    ssaver = StreamSaver(video_folder='unittest')
    time.sleep(4)
    ssaver.close()


def create_fake_file(filename='fakevideo.mp4'):
    with open(filename, 'w') as f:
        f.write('hej')
    return filename


def add_file_to_db(conn, abs_filepath):
    with conn.get_session() as session:
        f = File()
        f.filepath = str(abs_filepath)
        f.stream_nbr = 0
        f.start_date = datetime.now()
        f.end_date = datetime.now()
        f.num_frames = 10
        f.frame_offset = 0
        session.add(f)
        session.commit()

def add_bbox_to_db(conn):
    with conn.get_session() as session:
        b = BoundingBox()
        b.confidence = 0.1
        b.label = 'dummy'
        b.bbox = [1, 2, 3, 4]
        b.tbox = [1, 2, 3, 4]
        b.tracking_id = 1
        b.track_conf = 0.1

        frame = Frame()
        frame.file_id = 1
        frame.objects.append(b)
        frame.frame_number = 1
        frame.source_id = 0
        frame.timestamp = datetime.now()
        session.add(frame)
        session.commit()



def test_delete_videos():
    conn = init_connection()
    filename = create_fake_file()
    abs_filename = get_abs_filepath(filename)

    add_file_to_db(conn, abs_filename)
    add_bbox_to_db(conn)
    vp = Video_file_pruner(folder='.',
                           quarantinetime_d=0,
                           remove_videos_with_no_objects=True,
                           update_freq_s=0.1,
                           port=5433)
    vp.close()

    assert vp.video_quaranteen_time_is_passed(abs_filename)
    vp.quarantinetime_d = 1
    assert not vp.video_quaranteen_time_is_passed(abs_filename)
    assert vp.video_has_no_objects(abs_filename) == False
    time.sleep(0.1)
    with conn.get_session() as session:
        frame = session.scalars(select(Frame)).first()
        session.delete(frame)
        session.commit()
        #Frame.__table__.drop(session.bind)
    time.sleep(0.1)
    assert vp.video_has_no_objects(abs_filename) == True


def test_delete_videos_function():
    conn = init_connection()
    # Test delete file that are not pressent in database
    filename = create_fake_file()
    time.sleep(1.0)
    vp = Video_file_pruner(folder='.',
                           quarantinetime_d=0,
                           remove_videos_with_no_objects=True,
                           update_freq_s=0.1,
                           port=5433)
    time.sleep(1.0)
    vp.close()
    assert not Path(filename).exists()

    # test delete files that are pressent in database but has no objects
    filename = create_fake_file()
    vp = Video_file_pruner(folder='.',
                           quarantinetime_d=0,
                           remove_videos_with_no_objects=True,
                           update_freq_s=0.1,
                           port=5433)
    add_file_to_db(conn, filename)
    time.sleep(0.5)
    vp.close()
    assert not Path(filename).exists()

    # Do not delete files if they are not old enough
    filename = create_fake_file()
    vp = Video_file_pruner(folder='.',
                           quarantinetime_d=1,
                           remove_videos_with_no_objects=True,
                           update_freq_s=0.1,
                           port=5433)
    time.sleep(0.5)
    vp.close()
    assert Path(filename).exists()
    Path(filename).unlink()

    # do not delete files if they have objects linked to the frames
    conn.delete_tables()
    conn.create_tables()
    filename = create_fake_file()
    add_file_to_db(conn, filename)
    add_bbox_to_db(conn)

    vp = Video_file_pruner(folder='.',
                           quarantinetime_d=0,
                           remove_videos_with_no_objects=True,
                           update_freq_s=0.1,
                           port=5433)


    time.sleep(0.5)
    vp.close()
    assert Path(filename).exists()
    Path(filename).unlink()



def _test_min_disk_storage():
    pass
    # Skapa en fejk video-fil
    # Kolla nuvarande disk-storlek
    # Sätt quaranteen tid till 0 och
    # minsta disk-storlek till mindre än vad som är fritt nu
    # se att videon behålls

    # sätt minsta diskstorlek till sötrre än vad som är fritt nu.
    # se att videon tas bort.
