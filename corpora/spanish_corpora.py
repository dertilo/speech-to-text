import sys

sys.path.append(".")
import os
from os.path import join
from typing import NamedTuple, Dict
from util import data_io
from pathlib import Path

from corpora.heroico_usma import read_HEROICOandUSMA


class MailabsText(NamedTuple):
    original_text: str
    cleaned_text: str


def mailabs_data(path=".../m-ailabs-speech-dataset/es_ES",) -> Dict[str, MailabsText]:
    """
    59297 utterances
    """
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

    return {str(f): get_texts(f) for f in wavs}


def download_mailabs_corpus(file="es_ES.tgz"):
    url = "http://www.caito.de/data/Training/stt_tts"
    data_io.download_data(
        url, file, "m-ailabs_es", unzip_it=True, verbose=True,
    )


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

    return {str(f): get_text(f) for f in wavs}


def download_spanish_srl_corpora():
    """
    all together 18698 utterances
    :return:
    """
    dsnumer_abbrev = [
        ("71", "cl"),  # chilean
        ("72", "co"),  # colombian
        ("73", "pe"),  # peruvian
        ("74", "pr"),  # puerto rico
        ("75", "ve"),  # venezuelan
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


def common_voice_data(path):
    g = data_io.read_lines(join(path, "validated.tsv"))
    header = next(g).split("\t")

    def parse_line(l):
        d = {k: v for k, v in zip(header, l.split("\t"))}
        return d

    data = [parse_line(l) for l in g]
    return data


def common_voice_file2utt(path) -> Dict[str, str]:
    """
    112127 validated spanish utterances
    """
    key2utt = {d["path"]: d["sentence"] for d in common_voice_data(path)}
    utts = list(Path(path).rglob("*.mp3"))

    def get_key(f):
        return str(f).split("/")[-1]

    return {str(f): key2utt[get_key(f)] for f in utts if get_key(f) in key2utt.keys()}


def clean_text(text: str):
    return text.lower()


def build_text_corpus(base_path, corpus_file="spanish.txt"):
    file2utt = spanish_corpus(base_path)
    print("num files %d" % len(file2utt.keys()))
    print("num texts %d" % len(file2utt.values()))
    print("num unique texts %d" % len(set(file2utt.values())))
    data_io.write_lines(corpus_file, set(file2utt.values()))


def spanish_corpus(base_path):
    file2utt = {
        **read_openslr("%s/openslr" % base_path),
        **{
            k: v.original_text
            for k, v in mailabs_data(
                "%s/m-ailabs-speech-dataset/es_ES" % base_path
            ).items()
        },
        **read_HEROICOandUSMA("%s/LDC2006S37" % base_path),
        **common_voice_file2utt("%s/common_voice_es" % base_path),
    }
    file2utt = {f: clean_text(text) for f, text in file2utt.items()}
    return file2utt


if __name__ == "__main__":
    download_mailabs_corpus()
    # data = list(mailabs_data().values())
    # read_openslr('/home/tilo/gunther/data/asr_datasets/SLR72')
    # download_spanish_srl_corpora()

    # base_path = "/home/tilo/gunther"
    # base_path = "/docker-share/data/asr_datasets"
    # build_text_corpus(base_path)
