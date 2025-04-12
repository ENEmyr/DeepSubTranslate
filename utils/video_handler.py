import ffmpeg
from pathlib import Path
from utils.file_utils import is_video_file


def find_video_files(directory: Path):
    return [p for p in directory.rglob("*") if is_video_file(p)]


def has_target_subtitle(video_path: Path, target_language: str) -> bool:
    output = ffmpeg.probe(str(video_path))
    for stream in output.get("streams", []):
        if stream.get("codec_type") == "subtitle":
            lang = stream.get("tags", {}).get("language", "")
            if (
                lang.lower() == target_language.lower()[:2]
                or lang.lower() == target_language.lower()[:3]
                or lang.lower() == target_language.lower()
            ):
                return True
    return False


def embed_subtitle(
    video_path: Path, subtitle_info: list[tuple[Path, str, str]]
) -> None:
    # subtitle_info[0] = subtitle_path
    # subtitle_info[1] = subtitle_title
    # subtitle_info[2] = subtitle_language
    assert isinstance(video_path, Path), "video_path must be Path object"
    assert type(subtitle_info) == list, "subtitle_info must be list"

    output_path = video_path.with_name(
        video_path.stem + "_translated" + video_path.suffix
    )
    input_source = ffmpeg.input(str(video_path))
    input_video = input_source["v"]
    input_audio = input_source["a"]
    input_subtitles = []
    metadata = []
    for i, s_info in enumerate(subtitle_info):
        assert isinstance(s_info[0], Path), f"subtitle_info[0] must be Path object"
        assert isinstance(s_info[1], str), "subtitle_info[1] must be str"
        assert isinstance(s_info[2], str), "subtitle_info[2] must be str"
        input_subtitles.append(ffmpeg.input(str(s_info[0]))["s"])
        metadata.append((f"-metadata:s:s:{i}", "language", s_info[2]))
        metadata.append((f"-metadata:s:s:{i}", "title", s_info[1]))
    output_ffmpeg = ffmpeg.output(
        input_video,
        input_audio,
        *input_subtitles,
        str(output_path),
        vcodec="copy",
        acodec="copy",
    )
    # TODO fig metadata didn't show
    for meta_key, meta_field, meta_value in metadata:
        output_ffmpeg = output_ffmpeg.global_args(
            meta_key, f"{meta_field}={meta_value}"
        )
    output_ffmpeg.run(quiet=True, overwrite_output=True)


def extract_subtitle_stream(
    video_path: Path, output_path: Path | str, stream_index: int
) -> bool:
    try:
        (
            ffmpeg.input(str(video_path))
            .output(str(output_path), map=f"0:{stream_index}")
            .run(quiet=True, overwrite_output=True)
        )
    except ffmpeg.Error as e:
        print(f"Error extracting subtitle stream: {e}")
        return False
    return True


def extract_subtitles(
    video_path: Path, target_lang="english"
) -> list[tuple[Path, str]]:
    assert isinstance(video_path, Path), "video_path must be Path object"
    output = ffmpeg.probe(str(video_path))
    output_sub_paths = []
    for stream in output.get("streams", []):
        if stream.get("codec_type") == "subtitle":
            lang = stream.get("tags", {}).get("language", "")
            if (
                lang.lower() == target_lang.lower()[:2]
                or lang.lower() == target_lang.lower()[:3]
                or lang.lower() == target_lang.lower()
            ):
                stream_index = stream.get("index")
                codec_name = stream.get("codec_name")
                tag_title = (
                    stream.get("tags", {})
                    .get("title", str(stream_index))
                    .replace("[", "")
                    .replace("]", "")
                    .replace("(", "")
                    .replace(")", "")
                    .replace(" ", "-")
                    .replace(":", "-")
                    .replace("'", "")
                    .replace('"', "")
                    .replace("/", "-")
                    .replace("\\", "-")
                )
                output_sub_path = f"{video_path.stem}_{lang}_{tag_title}"
                if codec_name == "subrip":
                    output_sub_path += ".srt"
                elif codec_name == "ass":
                    output_sub_path += ".ass"
                # elif codec_name == "hdmv_pgs_subtitle":
                #     output_sub_path += ".pgs"
                else:
                    print(f"Unsupported subtitle codec: {codec_name}")
                    continue
                output_sub_path = video_path.with_name(output_sub_path)
                if extract_subtitle_stream(video_path, output_sub_path, stream_index):
                    output_sub_paths.append(
                        (
                            output_sub_path,
                            stream.get("tags", {}).get("title", str(stream_index)),
                        )
                    )
    return output_sub_paths
