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
        key = str(f).split("/")[-1]
        return key2text[key]

    file2text = {f: get_text(f) for f in wavs}
    return file2text


def download_spanish_srl_corpora():
    dsnumer_abbrev = [
        ("71", "cl"),# chilean
        ("72", "co"),# colombian
        ("73", "pe"),# peruvian
        ("74", "pr"),# puerto rico
        ("75", "ve"),# venezuelan
    ]
    for dsnumber, abbrev in dsnumer_abbrev:
        data_io.download_data(
            "https://www.openslr.org/resources/%s" % dsnumber,
            "es_%s_female.zip" % abbrev,
            "es_%s_female" % abbrev,
            unzip_it=True,
            do_raise=False,
            verbose=True,
        )
        data_io.download_data(
            "https://www.openslr.org/resources/%s" % dsnumber,
            "es_%s_male.zip" % abbrev,
            "es_%s_male" % abbrev,
            unzip_it=True,
            do_raise=False,
            verbose=True,
        )


if __name__ == "__main__":
    # data = mailabs_data()
    # read_openslr('/home/tilo/gunther/data/asr_datasets/SLR72')
    download_spanish_srl_corpora()
