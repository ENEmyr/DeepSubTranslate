from pathlib import Path
from utils.file_utils import is_video_file


def test_is_video_file_true():
    assert is_video_file(Path("test.mp4")) is True


def test_is_video_file_false():
    assert is_video_file(Path("test.txt")) is False
