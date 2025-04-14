import pysubs2
import re
from math import ceil
from pathlib import Path
from utils.deepseek import DeepSeekTranslator


class PreprocessSubtitle:
    SPECIAL_CHARS = ("\\N", "\\n", "\\h")

    def __init__(self, text: str):
        assert text, "text can't be an empty string"
        self._text = text
        self._open_block, self._close_block = self._extract_override_blocks()
        self._text = self._clean_text(self._text)

    @property
    def content(self) -> str:
        return self._text

    @content.setter
    def content(self, value: str) -> None:
        assert isinstance(value, str), "value must be a string"
        self._text = value

    @property
    def subtitle_line(self) -> str:
        return f"{self._open_block}{self._text}{self._close_block}"

    def _clean_text(self, text: str) -> str:
        for char in self.SPECIAL_CHARS:
            text = text.replace(char, "")
        return text.replace(self._open_block, "").replace(self._close_block, "")

    def _extract_override_blocks(self) -> tuple[str, str]:
        matches = re.findall(r"\{.*?\}", self._text)
        return (matches[0], matches[-1]) if matches else ("", "")


class PreprocessSubtitles:
    def __init__(self, events: list[pysubs2.ssaevent.SSAEvent]):
        assert events and isinstance(events, list), "Input must be a non-empty list"
        assert all(
            isinstance(e, pysubs2.ssaevent.SSAEvent) for e in events
        ), "All items must be SSAEvent instances"
        self._lines = [PreprocessSubtitle(event.text) for event in events]

    @property
    def contents(self) -> list[str]:
        return [line.content for line in self._lines]

    @contents.setter
    def contents(self, values: list[str]) -> None:
        assert isinstance(values, list), "Value must be a list of strings"
        for i, value in enumerate(values):
            if i >= len(self._lines):
                break
            if value == self._lines[i].content:
                continue
            if "<CNTL>" not in value:
                self._lines[i].content = value

    @property
    def subtitle_lines(self) -> list[str]:
        return [line.subtitle_line for line in self._lines]


def batch_list(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i : i + batch_size]


def translate_subtitle(
    sub_path: Path,
    dst: DeepSeekTranslator,
    progress_task,
    progress,
    output_path: str = "",
    batch_size: int = 100,
) -> Path:
    assert sub_path.suffix in (".srt", ".ass"), "Unsupported subtitle format"
    assert isinstance(batch_size, int) and batch_size > 0, "Invalid batch size"

    subtitle = pysubs2.load(str(sub_path))

    def update_progress(tl_type: str, text_in: str, text_out: str, i: int, total: int):
        progress.update(
            progress_task,
            description=f'[yellow]⏳ {tl_type} Translate "{text_in[:20]}..." => "{text_out[:20]}..." : ({i}/{total})',
        )

    if batch_size == 1:
        for i, line in enumerate(subtitle.events):
            processed = PreprocessSubtitle(line.text)
            translated = dst.translate(processed.content)
            update_progress(
                "", processed.content, translated, i + 1, len(subtitle.events)
            )
            if translated == processed.content:
                continue
            if "<CNTL>" not in translated:
                processed.content = translated
                line.text = processed.subtitle_line
    else:
        for i, batch in enumerate(batch_list(subtitle.events, batch_size)):
            offset = i * batch_size
            processed_batch = PreprocessSubtitles(batch)
            translated_texts = dst.translate(processed_batch.contents)
            update_progress(
                "Batch",
                processed_batch.contents[0],
                translated_texts[0],
                i + 1,
                ceil(len(subtitle.events) / batch_size),
            )
            try:
                processed_batch.contents = translated_texts
            except Exception as e:
                print(f"Error reassigning batch content: {e}")
                print(dst.get_chat_history())
                exit(1)
            for j, line_text in enumerate(processed_batch.subtitle_lines):
                subtitle.events[offset + j].text = line_text

    output_path = output_path or str(sub_path.with_name(f"translated{sub_path.suffix}"))
    subtitle.save(output_path)
    return Path(output_path)
