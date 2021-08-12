import sys

sys.path.append(".")
import difflib
import itertools
from dataclasses import dataclass
from typing import Optional, List

import librosa
import numpy as np
import torch
from nemo.collections.asr.parts.preprocessing import AudioSegment

from speech_to_text.transcribe_audio import SpeechToText, AlignedTranscript, LetterIdx

TARGET_SAMPLE_RATE = 16_000

if __name__ == "__main__":

    audio = AudioSegment.from_file(
        "/home/tilo/data/asr_data/GERMAN/tuda/raw/german-speechdata-package-v2/dev/2015-02-09-15-08-14_Samson.wav",
        target_sr=TARGET_SAMPLE_RATE,
        offset=0.0,
        trim=False,
    )
    asr = SpeechToText(
        model_name="jonatasgrosman/wav2vec2-large-xlsr-53-german",
    ).init()
    sm = difflib.SequenceMatcher()
    step = round(TARGET_SAMPLE_RATE * 5)
    previous: Optional[AlignedTranscript] = None
    letters: List[LetterIdx] = []

    for idx in range(0, len(audio.samples), step):
        array = audio.samples[idx : round(idx + 2 * step)]
        ts: AlignedTranscript = asr.transcribe_audio_array(array, audio.sample_rate)
        if previous is not None:
            right = AlignedTranscript(seq=[s for s in ts.seq if s.index < step])
            left = AlignedTranscript(seq=[s for s in previous.seq if s.index >= step])
            print(previous.text)
            sm.set_seqs(left.text, right.text)
            matches = [m for m in sm.get_matching_blocks() if m.size > 0]
            match_idx = np.argmin(
                [np.abs(m.a - round(len(left.text) / 2)) for m in matches]
            )
            m = matches[match_idx]
            print(f"{left.text[m.a:m.a + m.size]}->{right.text[m.b:m.b + m.size]}")
            glue_idx_left = m.a
            glue_idx_right = m.b
            letters_right = [
                LetterIdx(x.letter, x.index + idx)
                for x in right.seq
                if x.index < glue_idx_right
            ]
            letters_left = [
                LetterIdx(x.letter, x.index + idx - step)
                for x in left.seq
                if x.index >= glue_idx_left
            ]
            letters.extend(letters_left)
            letters.extend(letters_right)
            # print(f"left: {left.text}, right: {right.text}")
            print(
                f"GLUED left: {AlignedTranscript(letters_left).text}, right: {AlignedTranscript(letters_right).text}"
            )
        else:
            right = AlignedTranscript(seq=[s for s in ts.seq if s.index < step])
            print(f"initial: {right.text}")
            assert idx == 0
            letters.extend([x for x in right.seq])
        previous = ts

    transcript = AlignedTranscript(seq=letters)
    print(transcript.text)
    # print(transcript.array_idx)
    # print([i/TARGET_SAMPLE_RATE for i in transcript.array_idx])
