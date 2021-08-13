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

from speech_to_text.transcribe_audio import SpeechToText, AlignedTranscript, LetterIdx, \
    TARGET_SAMPLE_RATE


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

    import subprocess
    video_dir=sys.argv[1]
    asr = SpeechToText(
        model_name="jonatasgrosman/wav2vec2-large-xlsr-53-spanish",
    ).init()
    sm = difflib.SequenceMatcher()
    subtitles_dir="subtitles"
    if os.path.isdir(subtitles_dir):
        shutil.rmtree(subtitles_dir)
    os.makedirs(subtitles_dir)

    for video_file in Path(video_dir).glob("*.mp4"):
        file_name=video_file.stem
        with NamedTemporaryFile(suffix=".wav",delete=True) as tmp_file:
            command = f"ffmpeg -y -i '{video_file}' -ab 160k -ac 1 -ar 16000 -vn {tmp_file.name}" #
            subprocess.call(command, shell=True)

            audio = AudioSegment.from_file(
                tmp_file.name,
                target_sr=TARGET_SAMPLE_RATE,
                offset=0.0,
                trim=False,
            )
            print(audio.samples.shape)
        step = round(TARGET_SAMPLE_RATE * 5)
        arrays = generate_arrays(audio.samples,step)
        aligned_transcripts = [
            (idx, asr.transcribe_audio_array(array, TARGET_SAMPLE_RATE)) for idx, array in
            arrays
        ]
        transcript = glue_transcripts(aligned_transcripts, step=step)

        srt_blocks=[build_srt_block(idx,block,TARGET_SAMPLE_RATE) for idx,block in enumerate(generate_block(transcript.seq,block_len=10))]
        data_io.write_lines(f"{subtitles_dir}/{video_file.stem}.srt",srt_blocks)
