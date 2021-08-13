import datetime
import sys

from util import data_io

sys.path.append(".")
import difflib
import itertools
from dataclasses import dataclass
from typing import Optional, List, Tuple

import librosa
import numpy as np
import torch
from nemo.collections.asr.parts.preprocessing import AudioSegment

from speech_to_text.transcribe_audio import SpeechToText, AlignedTranscript, LetterIdx


def format_timedelta(milliseconds):
    return "0" + str(datetime.timedelta(milliseconds=milliseconds))[:-3].replace(
        ".", ","
    )


def build_srt_block(idx: int, letters: List[LetterIdx],sample_rate):
    start = round(1000 * letters[0].index / sample_rate)
    end = round(1000 * letters[-1].index / sample_rate)
    text = "".join((l.letter for l in letters))
    return f"""{idx}
{format_timedelta(start)} --> {format_timedelta(end)}
{text}
"""


# data_io.write_lines(f"sub.srt",[])
def generate_block(letters, block_len=10):
    buffer = []
    for l in letters:
        buffer.append(l)
        if len(buffer) > block_len and l.letter == " ":
            yield buffer
            buffer = []


if __name__ == '__main__':

    for idx,block in enumerate(generate_block(transcript.seq,block_len=10)):
        print(build_srt_block(idx,block))
