import os
from pathlib import Path
from typing import Tuple

from util import data_io

HOME = os.environ["HOME"]


def generate_audiofile_text_tuples(path:str)->Tuple[str,str]:
    p = Path(path)
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
