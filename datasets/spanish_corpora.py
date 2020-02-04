import os
from os.path import join
from typing import NamedTuple, Dict
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

def read_openslr(path) -> Dict[str, str]:
    wavs = list(Path(path).rglob("*.wav"))
    tsvs = list(Path(path).rglob("*.tsv"))

    def parse_line(l):
        file_name, text = l.split("\t")
        return file_name + ".wav", text

    key2text = {
        file_name: text
        for tsv_file in tsvs
        for file_name, text in (
            parse_line(l) for l in data_io.read_lines(join(path, str(tsv_file)))
        )
    }
    def get_text(f):
        key = str(f).split('/')[-1]
        return key2text[key]
    file2text = {f:get_text(f) for f in wavs}
    return file2text



if __name__ == "__main__":
    # data = mailabs_data()
    read_openslr('/home/tilo/gunther/data/asr_datasets/SLR72')
    print()
