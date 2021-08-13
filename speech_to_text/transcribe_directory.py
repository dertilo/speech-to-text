import os
import shutil
import sys

sys.path.append(".")

from pathlib import Path
from tempfile import NamedTemporaryFile

from util import data_io

from speech_to_text.asr_segment_glueing import generate_arrays, glue_transcripts

import difflib

from nemo.collections.asr.parts.preprocessing import AudioSegment

from speech_to_text.transcribe_audio import (
    SpeechToText,
    TARGET_SAMPLE_RATE,
)


if __name__ == "__main__":

    import subprocess

    video_dir = sys.argv[1]
    asr = SpeechToText(
        model_name="jonatasgrosman/wav2vec2-large-xlsr-53-spanish",
    ).init()
    sm = difflib.SequenceMatcher()
    output_dir = "transcripts"
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    for video_file in Path(video_dir).glob("*.mp4"):
        file_name = video_file.stem
        with NamedTemporaryFile(suffix=".wav", delete=True) as tmp_file:
            command = f"ffmpeg -y -i '{video_file}' -ab 160k -ac 1 -ar 16000 -vn {tmp_file.name}"  #
            subprocess.call(command, shell=True)

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
        data_io.write_lines(
            f"{output_dir}/{video_file.stem}.csv",
            [f"{l.letter}\t{l.index}" for l in transcript.seq],
        )
