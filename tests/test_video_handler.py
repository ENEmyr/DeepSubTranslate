import pytest
from pathlib import Path
from unittest.mock import patch
from utils.video_handler import has_target_subtitle


@patch("ffmpeg.probe")
def test_has_english_subtitle_found(mock_probe):
    mock_probe.return_value = {
        "streams": [
            {"codec_type": "subtitle", "tags": {"language": "eng"}},
            {"codec_type": "video"},
        ]
    }
    assert has_target_subtitle(Path("video.mkv"), "eng") is True


@patch("ffmpeg.probe")
def test_has_thai_subtitle_not_found(mock_probe):
    mock_probe.return_value = {
        "streams": [
            {"codec_type": "subtitle", "tags": {"language": "eng"}},
            {"codec_type": "video"},
        ]
    }
    assert has_target_subtitle(Path("video.mkv"), "tha") is False
