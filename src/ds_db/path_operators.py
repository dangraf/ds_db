from pathlib import Path
from typing import List
import os

__all__ = ['get_abs_filepath',
           'get_relative_path_from_file',
           'get_new_files',
           'get_machine_storage']


def get_abs_filepath(filepath: str = __file__) -> Path:
    p = Path(filepath)
    p = p.resolve()
    if p.is_dir():
        return p
    else:
        return p.parent


def get_relative_path_from_file(filepath, extra_path) -> Path:
    p = get_abs_filepath(filepath)
    p = p / extra_path
    return p


def get_new_files(path: Path, pattern: str, timestamp=float) -> List[str]:
    """
    returns a sorted list of files
    """
    path = Path(path)
    files = [f for f in path.glob(pattern) if f.stat().st_ctime > timestamp]
    files.sort(key=lambda x: x.stat().st_mtime)
    return files

def get_machine_storage():
    result=os.statvfs('/')
    block_size=result.f_frsize
    total_blocks=result.f_blocks
    free_blocks=result.f_bfree
    # giga=1024*1024*1024
    giga=1000*1000*1000
    total_size=total_blocks*block_size/giga
    free_size=free_blocks*block_size/giga
    ret = {'capacity_gb':total_size,
          'free_size_gb':free_size}
    return ret
