import random
import sys

import torchaudio
from tqdm import tqdm

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
    112127 validated spanish utterances minus 2 malpaudios
    """
    key2utt = {d["path"]: d["sentence"] for d in common_voice_data(path)}
    utts = list(Path(path).rglob("*.mp3"))

    def get_key(f):
        return str(f).split("/")[-1]

    malpaudios = ["common_voice_es_19499901.mp3","common_voice_es_19499893.mp3"] # broken audios

    return {
        str(f): key2utt[get_key(f)]
        for f in utts
        if get_key(f) in key2utt.keys() and str(f).split("/")[-1] not in malpaudios
    }


def clean_text(text: str):
    return text.upper()


def build_text_corpus(base_path, corpus_file="spanish.txt"):
    """
    num files 209140
    num texts 209140
    num unique texts 160317

    :param base_path:
    :param corpus_file:
    :return:
    """
    file2utt = spanish_corpus(base_path)
    print("num files %d" % len(file2utt.keys()))
    print("num texts %d" % len(file2utt.values()))
    print("num unique texts %d" % len(set(file2utt.values())))
    data_io.write_lines(corpus_file, set(file2utt.values()))


def spanish_corpus(base_path, check_audio=False):
    """

    :param base_path:
    :return:
    """

    def audio_is_loadable(f: str):
        try:
            data, fs = torchaudio.load(f)
            return True
        except Exception:
            print("file %s is broken!" % f)
            return False

    print("building corpus")
    file2utt = {
        **read_openslr("%s/openslr_spanish" % base_path),
        **{
            k: v.original_text
            for k, v in mailabs_data("%s/mailabs" % base_path).items()
        },
        **read_HEROICOandUSMA("%s/LDC2006S37" % base_path),
        **common_voice_file2utt("%s/common_voice_es" % base_path),
    }
    file2utt = {
        f: clean_text(text)
        for f, text in tqdm(file2utt.items())
        if not check_audio or audio_is_loadable(f)
    }
    return file2utt

def build_train_eval_set(base_path):
    data = list(
        spanish_corpus(base_path, check_audio=False).items())
    idx = list(range(len(data)))
    random.shuffle(idx)
    train_eval_split_idx = round(len(data) * 0.9)
    train_file, eval_file = 'spanish_train.jsonl','spanish_eval.jsonl'
    data_io.write_jsonl(train_file, [data[k] for k in idx[:train_eval_split_idx]])
    data_io.write_jsonl(eval_file, [data[k] for k in idx[train_eval_split_idx:]])

def build_train_eval_csvs(base_path):
    data = list(
        spanish_corpus(base_path, check_audio=False).items())
    def write_text_get_filename(file_name,text):
        prefix = os.path.splitext(file_name)[0]
        text_file_name = os.path.join(base_path,'spanish_texts',prefix)+'.txt'
        data_io.write_file(text_file_name, text)
        return text_file_name

    audio_text_files = [(file_name,write_text_get_filename(file_name,text)) for file_name, text in data]
    audio_text_files = [[os.path.join(base_path,x.split(base_path)[-1]) for x in t] for t in audio_text_files]

    idx = list(range(len(audio_text_files)))
    random.shuffle(idx)
    train_eval_split_idx = round(len(audio_text_files) * 0.9)
    train_file, eval_file = 'spanish_train.csv','spanish_eval.csv'
    data_io.write_lines(train_file, [','.join(audio_text_files[k]) for k in idx[:train_eval_split_idx]])
    data_io.write_lines(eval_file, [','.join(audio_text_files[k]) for k in idx[train_eval_split_idx:]])


if __name__ == "__main__":
    # data = list(mailabs_data().values())
    # read_openslr('/home/tilo/gunther/data/asr_datasets/SLR72')

    # base_path = "/home/tilo/gunther"
    base_path = os.path.join(os.environ["HOME"], "data/asr_data/SPANISH")
    # build_text_corpus(base_path)
    # build_train_eval_set(base_path)
    build_train_eval_csvs(base_path)
