from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, ARRAY, Integer, DateTime
from typing import List
from datetime import datetime, timedelta
from pathlib import Path
import cv2

__all__ = ['File',
           'Frame',
           'BoundingBox',
           'Classification']


def ntp_timestamp_to_datetime(ntp_timestamp):
    ts = ntp_timestamp / 1000000000
    return datetime.utcfromtimestamp(ts)


def bbox_info_to_array(bbox_info):
    x = bbox_info.org_bbox_coords.left
    y = bbox_info.org_bbox_coords.top
    h = bbox_info.org_bbox_coords.height
    w = bbox_info.org_bbox_coords.width
    return [int(x), int(y), int(w), int(h)]


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "file_table"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filepath: Mapped[str] = mapped_column(unique=True)
    stream_nbr: Mapped[int]
    frame_offset: Mapped[int]
    num_frames: Mapped[int]
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def update_from_filepath(self, filepath):
        p = Path(filepath)
        cap = cv2.VideoCapture(str(filepath))
        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            self.filepath = 0
            return
        duration = num_frames / fps
        print(duration)
        self.filepath = str(filepath)
        self.num_frames = num_frames
        self.stream_nbr = int(str(p).split('_')[-5].replace('stream', ''))
        self.frame_offset = 0
        self.end_date = datetime.fromtimestamp(p.stat().st_mtime)
        self.start_date = self.end_date - timedelta(seconds=duration)


class Frame(Base):
    __tablename__ = "frame_table"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("file_table.id"), nullable=True)
    source_id: Mapped[int]  # need both in file and frame since they are matched in a separate process
    frame_number: Mapped[int]
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    objects: Mapped[List["BoundingBox"]] = relationship(back_populates="frame", lazy="raise_on_sql",
                                                        cascade="delete, merge, save-update")

    def frame_meta2frame(self, frame_meta):
        self.source_id = int(frame_meta.source_id)
        self.frame_number = int(frame_meta.frame_num)
        self.timestamp = ntp_timestamp_to_datetime(frame_meta.ntp_timestamp)

    def __repr__(self):
        s = f"source_id: {self.source_id} \n frame_number: {self.frame_number} \n timestamp: {self.timestamp}"
        return s


class BoundingBox(Base):
    __tablename__ = "bbox_table"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    frame_id: Mapped[int] = mapped_column(ForeignKey("frame_table.id"), nullable=False)

    # tracking_id: Mapped[int] = mapped_column(ForeignKey("trackid_table.id"), nullable=False)
    tracking_id: Mapped[int]
    label: Mapped[str]
    confidence: Mapped[float]
    track_conf: Mapped[float]
    bbox: Mapped[List[int]] = mapped_column(ARRAY(Integer, as_tuple=False))
    tbox: Mapped[List[int]] = mapped_column(ARRAY(Integer, as_tuple=False))
    frame: Mapped["Frame"] = relationship(back_populates="objects", lazy="raise_on_sql",
                                          cascade="delete, merge, save-update")

    def obj_meta2bbox(self, obj_meta):
        self.label = obj_meta.obj_label
        self.confidence = obj_meta.confidence
        self.tracking_id = obj_meta.object_id
        self.track_conf = obj_meta.tracker_confidence
        self.bbox = bbox_info_to_array(obj_meta.detector_bbox_info)
        self.tbox = bbox_info_to_array(obj_meta.tracker_bbox_info)


class Classification(Base):
    __tablename__ = "classification_table"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_name: Mapped[str]
    tracking_id: Mapped[int]
    label: Mapped[str]
    confidence: Mapped[float]

    def cls_meta2classification(self, cls_meta, tracking_id, model_name):
        self.tracking_id = int(tracking_id)
        self.label = str(cls_meta.result_label)
        self.confidence = float(cls_meta.result_prob)
        self.model_name = str(model_name)
