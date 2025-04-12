import subprocess
from pathlib import Path
import shutil
import tempfile
import pytest


@pytest.fixture
def temp_video_folder():
    """
    Set up a temp directory with a test video (copy from assets/test.mp4 or mock).
    """
    temp_dir = tempfile.mkdtemp()
    test_video_src = Path("tests/assets/test_eng.mkv")
    test_video_dst = Path(temp_dir) / "test_eng.mkv"
    shutil.copy(test_video_src, test_video_dst)
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


def test_script_translates_and_embeds(temp_video_folder):
    """
    Full integration: run main.py on a test video and verify subtitle is embedded.
    """
    input_path = temp_video_folder
    script_path = Path("main.py").resolve()

    result = subprocess.run(
        ["python", str(script_path), "-p", str(input_path), "-s", "eng", "-t", "tha"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "Translated & embedded" in output or "Skipped" in output

    # Confirm output file was created
    output_file = input_path / "test_eng_translated.mkv"
    assert output_file.exists()
