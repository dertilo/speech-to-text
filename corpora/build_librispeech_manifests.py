import os
from os.path import join
from pathlib import Path

from util import data_io

HOME = os.environ["HOME"]


def build_jsonl_dataset(raw_data_path,folder):

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

    g = ((build_key(f), f) for f in audio_files)
    file_utt_g = (
        {"audio-file": str(f), "text": key2utt[k]} for k, f in g if k in key2utt.keys()
    )
    data_io.write_jsonl(join(raw_data_path,folder+"_manifest.jsonl"), file_utt_g)


if __name__ == "__main__":

    asr_path = HOME + "/data/asr_data"
    raw_data_path = asr_path + "/ENGLISH/LibriSpeech"

    for folder in os.listdir(raw_data_path):
        build_jsonl_dataset(raw_data_path,folder)
