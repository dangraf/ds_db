from sqlalchemy import func, update
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from ds_db.all import *
from typing import Dict

__all__ = ['StreamSaver',
           'Video_file_pruner']
PAD_PROBE_OK = 1


class Video_file_pruner:
    def __init__(self, folder: str,
                 quarantinetime_d: int,
                 remove_videos_with_no_objects: bool = True,
                 min_disk_space_gb=1,
                 update_freq_s=30,

                 **kwargs):
        """
        @folder: where video-files are stored
        @quarantine_time_d: Keep all files at least this time before they are removed from the system eg:
         quarantine_time_d=1 will not delete any video until 1 day old.

        @always_save_videos_with_objects: Will remove all video-chunks that contaion no objects if quarantine time
        is exeeded. Eg. quarantine=1, always_save_videos_with_objects=True, will keep all videos that have objects as
        long as possible
        @min_disk_space_gb: Minmum disk-space until oldest videos are removed.
        @kwargs: parameters for db connection
        """
        self.conn = DBConnection(**kwargs)
        self.stop_event = threading.Event()
        self.stop_event.clear()
        self.folder = folder
        self.quarantinetime_d = quarantinetime_d
        self.remove_videos_with_no_objects = remove_videos_with_no_objects
        self.min_disk_space_gb = min_disk_space_gb
        self.update_freq_s = update_freq_s

        self.thread = threading.Thread(target=self.check_videofiles)
        self.thread.start()

    def video_quaranteen_time_is_passed(self, file):
        file_mtime = file.stat().st_mtime
        dt_date = datetime.now() - datetime.fromtimestamp((file_mtime))

        # adding extra seconds to prevent removing unfinished videos and occations when
        # video-pruner is faster then Vidoe updater that adds videos to db
        if dt_date > timedelta(days=self.quarantinetime_d, seconds=self.update_freq_s):
            return True
        else:
            return False

    def video_has_no_objects(self, file):
        with self.conn.get_session() as s:
            c = s.query(Frame.frame_number).select_from(File).join(Frame).where(File.filepath == str(file)).count()
            if c == 0:
                return True
            else:
                return False

    def check_diskspace_and_remove_files(self, folder):
        print("check diskspace not implemented")
        while (get_machine_storage()['free_size_gb'] < self.min_disk_space_gb):
            files = get_new_files(path=self.folder, pattern='*.mp4', timestamp=0)
            Path(files[0]).unlink()

    def check_videofiles(self):
        while not self.stop_event.is_set():
            files = get_new_files(path=self.folder, pattern='*.mp4', timestamp=0)
            for file in files:
                print(file)
                if self.video_quaranteen_time_is_passed(file):
                    if self.video_has_no_objects(file):
                        print(f"removing file {str(file)}")
                        Path(file).unlink()
                    else:
                        print(f"keeping file {str(file)}")

            self.check_diskspace_and_remove_files(self.folder)

            time.sleep(self.update_freq_s)

    def close(self):
        self.stop_event.set()
        self.thread.join()


class FileUpdater:
    def __init__(self, video_folder, update_files_freq_s=2, **kwargs):
        self.update_files_freq_s = update_files_freq_s
        self.video_folder = video_folder
        self.conn = DBConnection(**kwargs)
        self.stop_event = threading.Event()
        self.stop_event.clear()
        self.frame_offsets = dict()
        self.TIME_SEARCH_MARGIN_S = 5
        self.TIME_AFTER_MOD_DATE_S = 1

        self.thread = threading.Thread(target=self.update_files_table_thread)
        self.thread.start()

    def close(self):
        self.stop_event.set()
        self.thread.join()

    def update_files_table_thread(self):
        folder = Path(self.video_folder)
        start_time = time.time()
        start_dt = datetime.fromtimestamp(start_time)
        while not self.stop_event.is_set():
            time.sleep(self.update_files_freq_s)
            files = get_new_files(path=folder, pattern='*.mp4', timestamp=start_time)
            with self.conn.get_session() as session:
                db_files = session.query(File.filepath).where(File.start_date > start_dt).all()
                db_files = flatten_array(db_files)
                for file in files:
                    mot_time_ts = file.stat().st_mtime
                    mod_time_dt = datetime.fromtimestamp(mot_time_ts)
                    if datetime.now() - mod_time_dt < timedelta(seconds=self.TIME_AFTER_MOD_DATE_S):
                        break
                    if str(file) not in db_files:
                        f = File()
                        f.update_from_filepath(file)
                        if f.filepath == 0:
                            # Something is wrong
                            continue
                        f_offset = self.frame_offsets.get(f.stream_nbr, 0)
                        f.frame_offset = f_offset
                        f_offset += f.num_frames
                        self.frame_offsets[f.stream_nbr] = f_offset
                        session.add(f)
                        session.commit()
                        session.refresh(f)
                        stmt = (update(Frame).where(Frame.source_id == f.stream_nbr,
                                                    Frame.timestamp > (
                                                            f.start_date - timedelta(
                                                        seconds=self.TIME_SEARCH_MARGIN_S)),
                                                    Frame.frame_number.between(f_offset - f.num_frames,
                                                                               f_offset)).values(file_id=f.id))
                        session.execute(stmt)
                        session.commit()
                        start_dt = mod_time_dt
                        start_time = mot_time_ts


class StreamSaver:
    def __init__(self, video_folder='dummy_folder',
                 update_files_freq_s=2,
                 compid_lookup: Dict = dict(),
                 **kwargs):
        """
        video_folder: where the video-files are stored
        update_files_freq_s: how often to check for new video-files
        compid_lookup: conversion between component_id (defined by gie-unique-id for the model) and a string
        """
        self.conn = DBConnection(**kwargs)
        self.session = self.conn.get_session()
        self.frames = dict()
        self.video_folder = video_folder
        self.trackid_offset = self.get_track_id_offset()
        self.update_files_freq_s = update_files_freq_s
        self.frame_offsets = dict()
        self.compid_lookup = compid_lookup

        self.fileupdater = FileUpdater(video_folder=video_folder,
                                       update_files_freq_s=update_files_freq_s,
                                       **kwargs)

        # https://docs.sqlalchemy.org/en/20/tutorial/orm_related_objects.html
        # Kolla här hur saker fungerar..

    def get_track_id_offset(self):

        offset = self.session.query(func.max(BoundingBox.tracking_id)).all()
        if offset[0][0] is None:
            return 0
        else:
            return offset[0][0] + 1

    def db_save_pad(self, pad, info, u_data):
        batch_meta = info2batchmeta(info)
        for frame_meta in iter_framelist(batch_meta):
            f = Frame()
            f.frame_meta2frame(frame_meta)
            for obj_meta in iter_objlist(frame_meta):
                o = BoundingBox()
                o.obj_meta2bbox(obj_meta)
                o.tracking_id += self.trackid_offset
                f.objects.append(o)
                for cid, cls in iter_classlist(obj_meta):
                    model_name = self.compid_lookup.get(cid, str(cid))
                    cl = Classification()
                    cl.cls_meta2classification(cls_meta=cls, tracking_id=o.tracking_id, model_name=model_name)
                    self.session.add(cl)

            if len(f.objects) > 0:
                self.session.add(f)
        self.session.commit()
        return PAD_PROBE_OK

    def close(self):
        self.fileupdater.close()
        self.session.close()
