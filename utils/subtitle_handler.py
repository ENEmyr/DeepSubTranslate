import pysubs2
from pathlib import Path
from utils.deepseek import DeepSeekTranslator


class PreprocessSubtitle:
    def __init__(self, text: str):
        # For ASS format
        # most of the time, the text is in the form of "{\\an8}sample \Ntext"
        # which is contains override block {} in front of the text
        # and may contain \N, \n or \h which is a special character in ass format
        # more detail : https://aegi.vmoe.info/docs/3.1/ASS_Tags/
        #
        # For srt format
        # mostly the text may be in form like '{\\i1}test\\Ntext,{\\i0}'

        assert len(text) > 0, "text can't be empty string"
        self._special_character = ("\\N", "\\n", "\\h")
        self._text = text
        self._open_block, self._close_block = self._extract_override_blocks()

        self._clean_special_character()
        self._text = self._text.replace(self._open_block, "").replace(
            self._close_block, ""
        )

    @property
    def content(self) -> str:
        return self._text

    @content.setter
    def content(self, value: str) -> None:
        assert type(value) == str, "value argument must be string"
        self._text = value

    @property
    def subtitle_line(self) -> str:
        return self._open_block + self._text + self._close_block

    def _clean_special_character(self) -> None:
        for spc in self._special_character:
            self._text = self._text.replace(spc, "")

    def _extract_override_blocks(self) -> tuple[str, str]:
        blocks = []
        idx = 0
        for c in self._text:
            if c == "{":
                blocks.append(c)
            elif len(blocks) - 1 == idx:
                blocks[idx] += c
                if c == "}":
                    idx += 1
            else:
                continue
        if len(blocks) == 0:
            return "", ""
        return blocks[0], blocks[-1]


class PreprocessSubtitles:
    def __init__(self, texts: list[pysubs2.ssaevent.SSAEvent]):
        assert len(texts) > 0, "texts can't be empty list"
        assert type(texts) == list, "texts must be list of SSAEvent"
        assert all(
            [isinstance(e, pysubs2.ssaevent.SSAEvent) for e in texts]
        ), "texts must be list of SSAEvent"
        self._lines = [PreprocessSubtitle(line.text) for line in texts]

    @property
    def contents(self) -> list[str]:
        return [line.content for line in self._lines]

    @contents.setter
    def contents(self, value: list[str]) -> None:
        assert (
            type(value) == list
        ), f"value argument must be list of string : {type(value)}"
        # assert len(value) == len(
        #     self._lines
        # ), f"value argument must be same length as lines: (lines, {len(self._lines)}) - (value, {len(value)})"
        for i, v in enumerate(value):
            assert type(v) == str, "value argument must be list of string"
            if i > len(self._lines) - 1:
                break
            if "<CNTL>" not in v:
                self._lines[i].content = v

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
    assert (
        sub_path.suffix == ".srt" or sub_path.suffix == ".ass"
    ), "Unsupported subtitle format"
    assert type(batch_size) == int, "batch size must be int"
    assert batch_size > 0, "batch size must be greater than 0"

    subtitle = pysubs2.load(str(sub_path))
    if batch_size == 1:
        for i, line in enumerate(subtitle.events):
            cleaned = PreprocessSubtitle(line.text)
            translate_text = dst.translate(cleaned.content)
            progress.update(
                progress_task,
                description=f'[yellow]⏳ Translate "{cleaned.content[:20]}..." => "{translate_text[:20]}..." : ({i+1}/{len(subtitle.events)})',
            )
            if "<CNTL>" not in translate_text:
                cleaned.content = translate_text
                line.text = cleaned.subtitle_line
    else:
        batches = list(batch_list(subtitle.events, batch_size))
        for i, batch in enumerate(batches):
            offset = i * batch_size
            cleaned_batch = PreprocessSubtitles(batch)
            translated_texts = dst.translate(cleaned_batch.contents)
            progress.update(
                progress_task,
                description=f'[yellow]⏳ Batch Translate "{cleaned_batch.contents[0][:20]}..." => "{translated_texts[0][:20]}..." : ({i+1}/{len(batches)})',
            )
            try:
                cleaned_batch.contents = translated_texts
            except Exception as e:
                print(
                    f"Error while tried to re-assign batch content in batch translation: {e}"
                )
                print(dst.get_chat_history())
                exit(1)
            for j, line in enumerate(cleaned_batch.subtitle_lines):
                subtitle.events[offset + j].text = line
    output_path = (
        str(sub_path.with_name(f"translated{sub_path.suffix}"))
        if output_path == ""
        else output_path
    )
    subtitle.save(output_path)
    return Path(output_path)
