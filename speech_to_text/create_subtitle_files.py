import datetime
import os
import shutil
import sys

sys.path.append(".")

from pathlib import Path
from tempfile import NamedTemporaryFile

from util import data_io

from speech_to_text.asr_segment_glueing import generate_arrays, glue_transcripts

import difflib
import itertools
from dataclasses import dataclass
from typing import Optional, List, Tuple

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
def generate_block(letters: List[LetterIdx]):
    buffer = []
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

    import subprocess

    video_dir = sys.argv[1]
    asr = SpeechToText(
        model_name="jonatasgrosman/wav2vec2-large-xlsr-53-spanish",
    ).init()
    sm = difflib.SequenceMatcher()
    subtitles_dir = "subtitles"
    if os.path.isdir(subtitles_dir):
        shutil.rmtree(subtitles_dir)
    os.makedirs(subtitles_dir)

    for video_file in Path(video_dir).glob("*.mp4"):
        file_name = video_file.stem
        with NamedTemporaryFile(suffix=".wav", delete=True) as tmp_file:
            command = f"ffmpeg -y -i '{video_file}' -ab 160k -ac 1 -ar 16000 -vn {tmp_file.name}"  #
            subprocess.call(command, shell=True)
            # with NamedTemporaryFile(suffix=".wav", delete=True) as processed_tmp_file:
            #
            #     command = f"sox {tmp_file.name} {processed_tmp_file.name} tempo 0.9" #
            #     subprocess.call(command, shell=True)

            audio = AudioSegment.from_file(
                tmp_file.name,
                target_sr=TARGET_SAMPLE_RATE,
                offset=0.0,
                trim=False,
            )
        step = round(TARGET_SAMPLE_RATE * 10)
        arrays = generate_arrays(audio.samples, step)
        aligned_transcripts = [
            (idx, asr.transcribe_audio_array(array, TARGET_SAMPLE_RATE))
            for idx, array in arrays
        ]
        transcript = glue_transcripts(aligned_transcripts, step=step)

        srt_blocks = [
            build_srt_block(idx, block, TARGET_SAMPLE_RATE)
            for idx, block in enumerate(generate_block(transcript.seq))
        ]
        data_io.write_lines(f"{subtitles_dir}/{video_file.stem}.srt", srt_blocks)
