import os
from pathlib import Path
from typing import Dict
from util import data_io


def librispeech_corpus(path: str) -> Dict[str, str]:
    ''':return dictionary where keys are filenames and values are utterances'''
    p = Path(path)
    audio_files = list(p.rglob("*.flac"))
    print('in %s found %d audio-files'%(path,len(audio_files)))
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

    g = ((f, build_key(f)) for f in audio_files)
    file2utt = {str(f): key2utt[k] for f, k in g if k in key2utt.keys()}
    return file2utt
