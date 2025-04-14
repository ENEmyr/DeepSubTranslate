import sys
import os
from argparse import ArgumentParser
from pathlib import Path
from rich.progress import Progress
from utils.video_handler import (
    find_video_files,
    has_target_subtitle,
    embed_subtitle,
    extract_subtitles,
)
from utils.subtitle_handler import translate_subtitle
from utils.file_utils import is_video_file
from utils.deepseek import DeepSeekTranslator

arg_parser = ArgumentParser(description="Process video files for subtitle translation.")
arg_parser.add_argument(
    "-p",
    "--path",
    dest="path",
    type=str,
    help="Path to video file or directory.",
    default=".",
)
arg_parser.add_argument(
    "-s",
    "--source_track",
    dest="source_track",
    type=str,
    help="Source subtitle track language (e.g., 'eng').",
    default="eng",
)
arg_parser.add_argument(
    "-t",
    "--target_track",
    dest="target_track",
    type=str,
    help="Target subtitle track language (e.g., 'tha').",
    default="tha",
)


def clean_files(files: list[str | Path]) -> None:
    try:
        for file in files:
            if os.path.exists(file):
                os.remove(file)
    except Exception as e:
        print(f"Error cleaning files {e}: {files}")


def process_video(
    file_path: Path,
    source_track: str,
    target_track: str,
    progress_task,
    progress: Progress,
):
    assert isinstance(file_path, Path), "file_path must be Path object"
    assert file_path.exists(), "file_path does not exist"

    if has_target_subtitle(file_path, target_track):
        progress.update(
            progress_task,
            advance=1,
            description=f"[green]✓ Skipped ({target_track} subtitle track exists): {file_path.name}",
        )
        return

    if not has_target_subtitle(file_path, source_track):
        progress.update(
            progress_task,
            advance=1,
            description=f"[red]✗ No {source_track} subtitle track: {file_path.name}",
        )
        return

    progress.update(
        progress_task, description=f"[yellow]⏳ Starting translation: {file_path.name}"
    )
    dst = DeepSeekTranslator()

    progress.update(
        progress_task, description=f"[yellow]⏳ Extracting subtitles: {file_path.name}"
    )
    clean_list = []

    source_subs = extract_subtitles(file_path, source_track)
    clean_list += [e[0] for e in source_subs]

    translated_subs = []

    for i, sub_info in enumerate(source_subs):
        # sub_info[0] = subtitle_path
        # sub_info[1] = subtitle_title
        progress.update(
            progress_task,
            description=f"[yellow]⏳ Translating ({i + 1}/{len(source_subs)}): {file_path.name}",
        )
        translated_sub = translate_subtitle(sub_info[0], dst, progress_task, progress)
        translated_subs.append((translated_sub, sub_info[1], target_track))
        clean_list.append(translated_sub)

    progress.update(
        progress_task,
        description=f"[yellow]⏳ Embedding {len(translated_subs)} subtitles : {file_path.name}",
    )
    embed_subtitle(file_path, translated_subs)

    progress.update(
        progress_task,
        description=f"[yellow]⏳ Cleaning temporary files: {file_path.name}",
    )
    clean_files(clean_list)

    progress.update(
        progress_task,
        advance=1,
        description=f"[blue]✔ Translated & embedded: {file_path.name}",
    )


def main():
    args = arg_parser.parse_args()
    video_files = []
    input_path = Path(args.path).resolve()
    assert input_path.exists(), "Path does not exist."

    if input_path.is_file() and is_video_file(input_path):
        video_files = [input_path]
    elif input_path.is_dir():
        video_files = find_video_files(input_path)
    else:
        print("Error: Invalid path or unsupported file.")
        sys.exit(1)

    if not video_files:
        print("Error: No video files found.")
        sys.exit(1)

    with Progress() as progress:
        task = progress.add_task("[cyan]Processing videos...", total=len(video_files))
        for video_file in video_files:
            process_video(
                Path(video_file), args.source_track, args.target_track, task, progress
            )


if __name__ == "__main__":
    main()
