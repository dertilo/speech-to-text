import datetime
import os
import shutil
import sys

from scipy.interpolate import interp1d

sys.path.append(".")

from pathlib import Path
from tempfile import NamedTemporaryFile

from util import data_io

from speech_to_text.asr_segment_glueing import generate_arrays, glue_transcripts

import difflib
import itertools
from dataclasses import dataclass
from typing import Optional, List, Tuple, Generator

import librosa
import numpy as np
import torch
from nemo.collections.asr.parts.preprocessing import AudioSegment

from speech_to_text.transcribe_audio import (
    SpeechToText,
    AlignedTranscript,
    LetterIdx,
    TARGET_SAMPLE_RATE,
)


def format_timedelta(milliseconds):
    return "0" + str(datetime.timedelta(milliseconds=milliseconds))[:-3].replace(
        ".", ","
    )


def build_srt_block(idx: int, letters: List[LetterIdx], sample_rate):
    start = round(1000 * letters[0].index / sample_rate)
    end = round(1000 * letters[-1].index / sample_rate)
    text = "".join((l.letter for l in letters))
    return f"""{idx}
{format_timedelta(start)} --> {format_timedelta(end)}
{text}
"""


# data_io.write_lines(f"sub.srt",[])
def cut_transcript_at_pauses(letters: List[LetterIdx]) -> Generator[List[LetterIdx]]:
    """
    for better visualization in video cut aligned transcript into segments separated ideally by pauses,
    so that transcitions between subtitle-block are not too anoying
    """
    buffer: List[LetterIdx] = []
    block_end = letters[0].index

    for k, l in enumerate(letters):
        if l.letter == " ":
            next_one = min(k + 1, len(letters))
            is_pause = (
                letters[next_one].index - buffer[-1].index > 0.25 * TARGET_SAMPLE_RATE
            )
            if is_pause and len(buffer) > 10 or len(buffer) > 50:
                buffer[0].index = (
                    block_end + 10
                )  # shift block-start back in time, shortly after last block-end in order to use pause for "reading" the transcript even before it is spoken
                yield buffer
                block_end = buffer[-1].index
                buffer = []
            else:
                buffer.append(l)
        else:
            buffer.append(l)

    buffer[0].index = (
        block_end + 10
    )  # shift block-start back in time, shortly after last block-end in order to use pause for "reading" the transcript even before it is spoken
    yield buffer


if __name__ == "__main__":

    transript_dir = sys.argv[1]

    sm = difflib.SequenceMatcher()
    subtitles_dir = f"{transript_dir}/subtitles"
    if os.path.isdir(subtitles_dir):
        shutil.rmtree(subtitles_dir)
    os.makedirs(subtitles_dir)

    for transcript_file in Path(transript_dir).glob("*.csv"):
        file_name = transcript_file.stem
        g = (line.split("\t") for line in data_io.read_lines(str(transcript_file)))
        letters = [LetterIdx(l, int(i)) for l, i in g]
        raw_transcript = "".join([l.letter for l in letters])

        corrected_transcript_file = str(transcript_file).replace(".csv", ".txt")
        if os.path.isfile(corrected_transcript_file):
            corrected_transcript = list(data_io.read_lines(corrected_transcript_file))[
                0
            ]
            if corrected_transcript != "".join([l.letter for l in letters]):
                sm.set_seqs(raw_transcript, corrected_transcript)
                matches = [m for m in sm.get_matching_blocks() if m.size > 0]

                matched2index = {
                    m.b + k: letters[m.a + k].index
                    for m in matches
                    for k in range(m.size)
                }
                x = list(matched2index.keys())
                y = list(matched2index.values())
                interp_fun = interp1d(x, y)
                letters = [
                    LetterIdx(l, int(matched2index.get(k, interp_fun(k))))
                    for k, l in enumerate(corrected_transcript)
                ]

        srt_blocks = [
            build_srt_block(idx, block, TARGET_SAMPLE_RATE)
            for idx, block in enumerate(cut_transcript_at_pauses(letters))
        ]
        data_io.write_lines(f"{subtitles_dir}/{transcript_file.stem}.srt", srt_blocks)
