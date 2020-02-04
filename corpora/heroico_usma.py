import os
from os.path import join
from pathlib import Path

from util import data_io


def read_HEROICOandUSMA(path=".../LDC2006S37"):
    """
    overall 6_370 unique (textual) utterances; 19_020 recordings
    the read speech prompts are listed in two files in the transcripts directory:
    HEROICO- Recordings.txt and USMA-prompts.txt
    containing the sentences read by informants at the Mexican Military Academy and USMA
    separated by a tab, the first denoting the base name of the waveform file, and the second the prompt used in recording the utterence

    Some of the USMA informants wore an additional throat microphone. That data was recorded in a separate stream and stored in files whose names begin with the letter t.
    """
    heroico_answers = build_file2utt_heroico_answers(path)
    heroico_recordings = build_file2utterance_heroico_recordings(path)
    usma_recordings = build_file2utterance_usma(path)

    file2utt = {**heroico_answers, **heroico_recordings, **usma_recordings}
    return file2utt


def build_file2utt_heroico_answers(path):
    heroico_answers = "data/transcripts/heroico-answers.txt"
    heroico_answers_path = "data/speech/heroico/Answers_Spanish"
    file2utt = {
        join(path, heroico_answers_path, f_name) + ".wav": utt
        for f_name, utt in (
            l.replace("\r", "").split("\t")
            for l in data_io.read_lines(
                join(path, heroico_answers), encoding="iso-8859-1"
            )
        )
    }
    assert not any([d is None for d in file2utt.values()])
    assert all((os.path.isfile(wav_file) for wav_file in file2utt.keys()))
    return file2utt


def build_file2utterance_heroico_recordings(path):
    heroico_recordings = "data/transcripts/heroico-recordings.txt"
    heroico_recordings_path = "data/speech/heroico/Recordings_Spanish"
    key2utt = {
        key: utt
        for key, utt in (
            l.replace("\r", "").split("\t")
            for l in data_io.read_lines(
                join(path, heroico_recordings), encoding="iso-8859-1"
            )
        )
    }

    def get_utterance(f):
        key = str(f).split("/")[-1].replace(".wav", "")
        return key2utt[key]

    wavs = list(Path(join(path, heroico_recordings_path)).rglob("*.wav"))
    file2utt = {str(f): get_utterance(f) for f in wavs}
    assert all([f.endswith(".wav") for f in file2utt.keys()])
    return file2utt


def build_file2utterance_usma(path):
    usma_prompts = "data/transcripts/usma-prompts.txt"
    usma_prompts_path = "data/speech/usma"

    key2utt = {
        key.replace("s", ""): utt
        for key, utt in (
            l.replace("\r", "").split("\t")
            for l in data_io.read_lines(join(path, usma_prompts), encoding="iso-8859-1")
        )
    }

    def get_usma_utterance(f):
        key = (
            str(f).split("/")[-1].replace(".wav", "").replace("s", "").replace("t", "")
        )
        return key2utt[key]

    wavs = list(Path(join(path, usma_prompts_path)).rglob("*.wav"))

    file2utt = {str(f): get_usma_utterance(f) for f in wavs}
    assert all([f.endswith(".wav") for f in file2utt.keys()])
    return file2utt


if __name__ == "__main__":
    file2utt = read_HEROICOandUSMA("/home/tilo/gunther/data/asr_datasets/LDC2006S37")
    print(len(set(file2utt.keys())))
