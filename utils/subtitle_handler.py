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


def translate_subtitle(
    sub_path: Path,
    dst: DeepSeekTranslator,
    progress_task,
    progress,
    output_path: str = "",
) -> Path:
    # TODO: batch translate
    assert (
        sub_path.suffix == ".srt" or sub_path.suffix == ".ass"
    ), "Unsupported subtitle format"
    subtitle = pysubs2.load(str(sub_path))
    for i, line in enumerate(subtitle.events):
        cleaned = PreprocessSubtitle(line.text)
        translate_text = dst.translate(cleaned.content)
        progress.update(
            progress_task,
            description=f"[yellow]⏳ Translate {cleaned.content[:20]}... => {translate_text[:20]}... : ({i+1}/{len(subtitle.events)})",
        )
        cleaned.content = translate_text
        line.text = cleaned.subtitle_line
    output_path = (
        str(sub_path.with_name(f"translated{sub_path.suffix}"))
        if output_path == ""
        else output_path
    )
    subtitle.save(output_path)
    return Path(output_path)
