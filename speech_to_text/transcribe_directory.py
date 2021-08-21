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
    AlignedTranscript,
)


def convert_to_wav_transcribe(asr, file) -> AlignedTranscript:
    with NamedTemporaryFile(suffix=".wav", delete=True) as tmp_file:
        command = (
            f"ffmpeg -y -i '{file}' -ab 160k -ac 1 -ar 16000 -vn {tmp_file.name}"  #
        )
        subprocess.call(command, shell=True)

        transcript = transcribe_audio_file(asr, tmp_file.name)
    return transcript


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

    for file in Path(input_dir).glob("*.wav"):  # mp4, m4a
        transcript = transcribe_audio_file(asr, file)
        # transcript = convert_to_wav_transcribe(asr, file)
        data_io.write_lines(
            f"{output_dir}/{file.stem}.csv",
            [f"{l.letter}\t{l.index}" for l in transcript.letters],
        )

        data_io.write_lines(
            f"{output_dir}/{file.stem}.txt",
            ["".join([l.letter for l in transcript.letters])],
        )
