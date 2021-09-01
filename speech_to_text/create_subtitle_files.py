import datetime
import os
import re
import shutil
import sys
from dataclasses import dataclass

from pysubs2 import SSAFile, Color, SSAEvent
from pysubs2.time import make_time
from scipy.interpolate import interp1d
from text_processing.smith_waterman_alignment import smith_waterman_alignment

sys.path.append(".")

from pathlib import Path

from util import data_io

import difflib
from typing import List, Generator, Tuple, Dict

from speech_to_text.transcribe_audio import (
    LetterIdx,
    TARGET_SAMPLE_RATE,
)


def format_timedelta(milliseconds):
    return "0" + str(datetime.timedelta(milliseconds=milliseconds))[:-3].replace(
        ".", ","
    )


def build_srt_block(
    idx: int,
    blocks: Dict[str, List[LetterIdx]],
    sample_rate,
):

    subtitle_texts = []
    start, end = None, None
    colors = ["#ffffff", "#ff0000", "#0019ff", "#0fff00"]
    for k, (name, block) in enumerate(blocks.items()):
        if len(block) > 0:
            if start is None:
                start = round(1000 * block[0].r_idx / sample_rate)
                end = round(1000 * block[-1].r_idx / sample_rate)
            text = "".join((l.letter for l in block))
        else:
            text = ""
            print("WARNING! empty block!")
        subtitle_texts.append(f"<font color='{colors[k]}'>{text}</font>")
    subtitle = "\n".join(subtitle_texts)
    return f"""{idx}
{format_timedelta(start)} --> {format_timedelta(end)}
{subtitle}
"""


def cut_block_out_of_transcript(
    transcripts: List[Tuple[str, List[LetterIdx]]], block_start, block_end
):
    def tokenize_letters(lettas: List[LetterIdx]):
        buffer = []
        for l in lettas:
            if l.letter != FORCE_BREAK:
                buffer.append(l)
            if l.letter == " ":
                yield buffer
                buffer = []
        if len(buffer)>0:
            yield buffer

    name2block = {
        name: [
            l
            for tok in tokenize_letters(letters)
            if tok[0].r_idx >= block_start and tok[0].r_idx < block_end
            for l in tok
        ]
        for name, letters in transcripts
    }
    return name2block


FORCE_BREAK = "|"


def generate_block_start_ends(
    letters: List[LetterIdx],
) -> Generator[int, None, None]:
    """
    for better visualization in video cut aligned transcript into segments separated ideally by pauses,
    so that transcitions between subtitle-block are not too anoying
    """
    block_len: int = 0
    last_end = 0
    for k, l in enumerate(letters):
        block_len += 1
        force_break = l.letter == FORCE_BREAK
        if force_break:
            print(f"DEBUG: foreced break after: {l.letter}")
        if l.letter == " " or force_break:
            next_one = min(
                k + 2, len(letters)
            )  # next token might start with vocal, heuristic to get at "real" start of token
            is_pause = letters[next_one].r_idx - l.r_idx > 0.25 * TARGET_SAMPLE_RATE
            if (is_pause and block_len > 10 or block_len > 90) or force_break:
                yield last_end, l.r_idx
                last_end = l.r_idx + 10
                block_len = 0
    yield last_end, l.r_idx


@dataclass
class SubtitleBlock:
    start: int  # in ms
    end: int  # in ms
    name_texts: List[Tuple[str, str]]

    @property
    def names(self):
        return [n for n, _ in self.name_texts]

    @classmethod
    def from_dict_letters(cls, dictletter: Dict[str, List[LetterIdx]]):
        first_index = list(dictletter.values())[0][0].r_idx
        start = make_time(ms=round(1000 * first_index / TARGET_SAMPLE_RATE))
        last_index = list(dictletter.values())[0][-1].r_idx
        end = make_time(ms=round(1000 * last_index / TARGET_SAMPLE_RATE))
        return cls(
            start,
            end,
            [
                (name, "".join((l.letter for l in letters)))
                for name, letters in dictletter.items()
            ],
        )

@dataclass
class StyleConfig:
    fontsize:float=20.0

def create_ass_file(subtitle_blocks: List[SubtitleBlock], ass_file,styles:Dict[str,StyleConfig]):
    subs = SSAFile()
    colors = [Color(255, 255, 255), Color(100, 100, 255), Color(255, 100, 100)]
    for k, name in enumerate(subtitle_blocks[0].names):
        my_style = subs.styles["Default"].copy()
        my_style.primarycolor = colors[k]
        my_style.fontsize=styles[name].fontsize
        my_style.shadow=0
        subs.styles[name] = my_style

    for sb in subtitle_blocks:
        start, end = None, None
        for name, text in sb.name_texts:
            if len(text) > 0:
                text=text.replace("_"," ")
                if start is None:
                    start = sb.start
                    end = sb.end
                sub_line = SSAEvent(
                    start=start,
                    end=end,
                    text=text,
                )
                sub_line.style = name
                subs.append(sub_line)
            else:
                print(f"WARNING: got empty block! {name} ")
    subs.save(ass_file)


@dataclass
class TranslatedTranscript:
    """
    is to be aligned an cut into blocks to form subtitles together with verbatim transcript
    """

    name: str
    order: int
    text: str


def segment_transcript_to_subtitle_blocks(
    transcript_letters_csv, translated_transcript: List[TranslatedTranscript]
) -> List[Dict[str, List[LetterIdx]]]:
    g = (line.split("\t") for line in data_io.read_lines(str(transcript_letters_csv)))
    raw_letters = [LetterIdx(l, int(i)) for l, i in g]
    assert all(
        (
            raw_letters[k].r_idx > raw_letters[k - 1].r_idx
            for k in range(1, len(raw_letters))
        )
    )

    subtitles = []
    letters = raw_letters
    for tt in sorted(translated_transcript, key=lambda x: x.order):
        aligned_letters = temporal_align_text_to_letters(tt.text, letters)
        subtitles.append((tt.name, aligned_letters))
        letters = aligned_letters  # align next transcript on already aligned, heuristic is to use language-similarities: native->spanish->english->german

    _, first_aligned = subtitles[0]
    named_blocks = [
        cut_block_out_of_transcript(subtitles, s, e)
        for s, e in generate_block_start_ends(first_aligned)
    ]
    return named_blocks


def create_timestamp(index):
    return make_time(ms=round(1000 * index / TARGET_SAMPLE_RATE))


def regex_tokenizer(
    text, pattern=r"\w+(?:'\w+)?|[^\w\s]"
) -> List[Tuple[int, int, str]]:  # pattern stolen from scikit-learn
    return [(m.start(), m.end(), m.group()) for m in re.finditer(pattern, text)]


def temporal_align_text_to_letters(
    corrected_transcript: str,
    raw_letters: List[LetterIdx],
):
    START = "<start>"
    END = "<end>"
    add_start_end = lambda x: f"{START}{x}{END}"
    raw_letters = (
        [LetterIdx(s, raw_letters[0].r_idx) for s in START]
        + raw_letters
        + [LetterIdx(s, raw_letters[-1].r_idx) for s in END]
    )

    raw_transcript = "".join([l.letter for l in raw_letters])
    # raw_transcript = add_start_end(raw_transcript)
    corrected_transcript = add_start_end(corrected_transcript)
    corrected_transcript = re.sub(r"\n+", f" {FORCE_BREAK} ", corrected_transcript)
    # sm.set_seqs(raw_transcript, corrected_transcript)
    # matches = [m for m in sm.get_matching_blocks() if m.size > 0]
    tokens_a = regex_tokenizer(raw_transcript)
    tokens_b = regex_tokenizer(corrected_transcript)
    # print(f"tokenized translated-transcript: {' '.join(x for _,_,x in tokens_b)}")
    tok2letter_idx_a = {k: start_idx for k, (start_idx, _, _) in enumerate(tokens_a)}
    tok2letter_idx_a[len(tokens_a)] = len(raw_transcript) + 1
    tok2letter_idx_b = {k: start_idx for k, (start_idx, _, _) in enumerate(tokens_b)}
    tok2letter_idx_b[len(tokens_b)] = len(corrected_transcript) + 1

    alignments, _ = smith_waterman_alignment(
        [t.lower() for _, _, t in tokens_a], [t.lower() for _, _, t in tokens_b]
    )
    matches = [al for al in alignments if al.ref == al.hyp]
    print_for_debug(matches, raw_transcript, tok2letter_idx_a)

    raw_letters += [raw_letters[-1]]
    matched2index = {
        tok2letter_idx_b[al.hypi_from]
        + k: raw_letters[tok2letter_idx_a[al.refi_from] + k].r_idx
        for al in matches
        for k in range(tok2letter_idx_a[al.refi_to] - tok2letter_idx_a[al.refi_from])
    }
    x = list(matched2index.keys())
    y = list(matched2index.values())
    interp_fun = interp1d(x, y)
    letters = [
        LetterIdx(l, int(matched2index.get(k, interp_fun(k))))
        for k, l in enumerate(corrected_transcript)
    ]
    assert all(
        (letters[k].r_idx >= letters[k - 1].r_idx for k in range(1, len(letters)))
    )
    return letters[len(START) : -len(END)]


def print_for_debug(matches, raw_transcript, tok2letter_idx_a):
    bold_text = raw_transcript
    for al in sorted(matches, key=lambda m: -m.refi_from):
        start_idx = tok2letter_idx_a[al.refi_from]
        size = tok2letter_idx_a[al.refi_to] - tok2letter_idx_a[al.refi_from]
        bold_text = (
            bold_text[:start_idx]
            + f"\033[1m{bold_text[start_idx:(start_idx + size)]}\033[0m"
            + bold_text[start_idx + size :]
        )
    print(bold_text)


if __name__ == "__main__":

    transript_dir = sys.argv[1]
    manual_transcripts_dir = sys.argv[2]

    list(create_subtitles(transript_dir, manual_transcripts_dir))
