import os
from os.path import join
from pathlib import Path

import torchaudio
from tqdm import tqdm
from util import data_io

HOME = os.environ["HOME"]


def generate_audiofile_text_tuples(raw_data_path, folder):

    p = Path(join(raw_data_path, folder))
    audio_files = list(p.rglob("*.flac"))

    def parse_line(l):
        s = l.split(" ")
        return s[0], " ".join(s[1:])

    g = (
        parse_line(l)
        for f in p.rglob("*.trans.txt")
        for l in data_io.read_lines(str(f))
    )
    key2utt = {k: v for k, v in g}

    def build_key(f):
        return str(f).split("/")[-1].replace(".flac", "")

    for f in audio_files:
        k = build_key(f)
        if k in key2utt.keys():
            text = key2utt[k]
            audio_file = str(f)
            yield audio_file, text


MILLISECONDS_TO_SECONDS = 0.001


def get_length(audio_file):
    si, ei = torchaudio.info(audio_file)
    length_ms = int(si.length / si.channels / si.rate / MILLISECONDS_TO_SECONDS)
    return length_ms


if __name__ == "__main__":

    asr_path = HOME + "/data/asr_data"
    raw_data_path = asr_path + "/ENGLISH/LibriSpeech"

    for folder in next(os.walk(raw_data_path))[1]:
        print(folder)
        g = generate_audiofile_text_tuples(raw_data_path, folder)
        file_utt_g = (
            {
                "audio-file": audio_file,
                "text": text,
                "length_ms": get_length(audio_file),
            }
            for audio_file, text in tqdm(g)
        )
        data_io.write_jsonl(join(raw_data_path, folder + "_manifest.jsonl"), file_utt_g)
