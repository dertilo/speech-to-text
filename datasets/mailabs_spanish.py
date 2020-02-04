import os
from os.path import join
from typing import NamedTuple
from util import data_io
from pathlib import Path


class MailabsText(NamedTuple):
    original_text: str
    cleaned_text: str


def mailabs_data(
    path="/home/tilo/gunther/data/asr_datasets/m-ailabs-speech-dataset/es_ES",
):
    jsons = [str(p) for p in Path(path).rglob("*.json")]
    key2texts = {
        f: MailabsText(d["original"], d["clean"])
        for json in jsons
        for f, d in data_io.read_json(json).items()
    }

    wavs = list(Path(path).rglob("*.wav"))

    def get_texts(f):
        key = str(f).split("/")[-1].replace(" copy", "")
        return key2texts[key]

    return {f: get_texts(f) for f in wavs}


if __name__ == "__main__":
    data = mailabs_data()
    print()
