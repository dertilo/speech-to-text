import os
import shutil
import sys

sys.path.append(".")

from pathlib import Path
from tempfile import NamedTemporaryFile

from util import data_io

from speech_to_text.asr_segment_glueing import transcribe_audio_file

from speech_to_text.transcribe_audio import (
    SpeechToText,
)

if __name__ == "__main__":

    import subprocess

    model = sys.argv[1]
    input_dir = sys.argv[2]
    output_dir = sys.argv[3]

    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    asr = SpeechToText(
        model_name=model,
    ).init()

    for video_file in Path(input_dir).glob("*.m*"):  # mp4, m4a
        file_name = video_file.stem
        with NamedTemporaryFile(suffix=".wav", delete=True) as tmp_file:
            command = f"ffmpeg -y -i '{video_file}' -ab 160k -ac 1 -ar 16000 -vn {tmp_file.name}"  #
            subprocess.call(command, shell=True)

            transcript = transcribe_audio_file(asr, tmp_file.name)

        data_io.write_lines(
            f"{output_dir}/{video_file.stem}.csv",
            [f"{l.letter}\t{l.index}" for l in transcript.seq],
        )

        data_io.write_lines(
            f"{output_dir}/{video_file.stem}.txt",
            ["".join([l.letter for l in transcript.seq])],
        )
