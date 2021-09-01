import os
import pickle
import sys

import icdiff
from util import data_io

sys.path.append(".")
import difflib
from typing import Optional, List, Tuple

import numpy as np
from nemo.collections.asr.parts.preprocessing import AudioSegment

from speech_to_text.transcribe_audio import (
    SpeechToText,
    AlignedTranscript,
    LetterIdx,
    TARGET_SAMPLE_RATE,
)


def glue_transcripts(
    aligned_transcripts: List[AlignedTranscript],
    debug=True,
) -> AlignedTranscript:
    all_but_last_must_be_of_same_len = (
        len(set((len(x.letters) for x in aligned_transcripts[:-1]))) == 1
    ), [len(x.letters) for x in aligned_transcripts]
    assert all_but_last_must_be_of_same_len

    sm = difflib.SequenceMatcher()
    sample_rate = None
    previous: Optional[AlignedTranscript] = None
    letters: List[LetterIdx] = []
    for ts in aligned_transcripts:
        if sample_rate is None:
            sample_rate = ts.sample_rate
        if previous is not None:
            glued = glue_left_right(left=previous, right=ts, sm=sm, debug=debug)
            print(f"prev-start_idx: {glued.abs_idx(glued.letters[0])}")
            letters = [
                l for l in letters if l.r_idx < glued.abs_idx(glued.letters[0])
            ]
            letters.extend(
                [LetterIdx(l.letter, glued.abs_idx(l)) for l in glued.letters]
            )
        else:
            right = ts
            if debug:
                print(f"initial: {right.text}")
            assert ts.start_idx == 0
            letters.extend(
                [LetterIdx(x.letter, right.abs_idx(x)) for x in right.letters]
            )
        previous = ts

    assert all(
        (letters[k].r_idx > letters[k - 1].r_idx for k in range(1, len(letters)))
    )
    assert aligned_transcripts[0].start_idx == 0
    transcript = AlignedTranscript(
        letters, sample_rate, start_idx=aligned_transcripts[0].start_idx
    )
    return transcript


def glue_left_right(
    left: AlignedTranscript,
    right: AlignedTranscript,
    sm: difflib.SequenceMatcher,
    debug=False,
) -> AlignedTranscript:
    """
    two overlapping sequences

    left:_____----:-
    right:_______-:----

    colon is glue-point which is to be found

    1. from left cut away what reaches too far into past
        left:________-:-
    2. from right cut away what reaches too far into future -> just for alignmend-method
        right:_______-:--

    return cut left and full right glued together
    """

    sr = right.sample_rate
    assert sr == left.sample_rate

    left = AlignedTranscript(
        letters=[s for s in left.letters if left.abs_idx(s) >= right.start_idx],
        sample_rate=sr,
        start_idx=left.start_idx,
    )

    cut_right_just_to_help_alingment = AlignedTranscript(
        [
            l
            for l in right.letters
            if right.abs_idx(l) < left.abs_idx(left.letters[-1])
        ],
        sr,
        right.start_idx,
    )
    sm.set_seqs(left.text, cut_right_just_to_help_alingment.text)
    matches = [m for m in sm.get_matching_blocks() if m.size > 0]
    aligned_idx = [(m.a + k, m.b + k) for m in matches for k in range(m.size)]
    match_idx_closest_to_middle = np.argmin(
        [np.abs(i - round(len(left.text) / 2)) for i, _ in aligned_idx]
    )
    glue_left, glue_right = aligned_idx[match_idx_closest_to_middle]
    glue_idx_left = left.letters[glue_left].r_idx
    glue_idx_right = right.letters[glue_right].r_idx
    letters_right = [
        LetterIdx(x.letter, x.r_idx + right.start_idx - left.start_idx)
        for x in right.letters
        if x.r_idx > glue_idx_right
    ]
    letters_left = [x for x in left.letters if x.r_idx <= glue_idx_left]
    if debug:
        print(f"left: {left.text}, right: {right.text}")
        print(
            f"GLUED left: {AlignedTranscript(letters_left, sr).text}, right: {AlignedTranscript(letters_right, sr).text}"
        )
    return AlignedTranscript(letters_left + letters_right, sr, start_idx=left.start_idx)


def generate_arrays(samples: np.ndarray, step):
    for idx in range(0, len(samples), step):
        segm_end_idx = round(idx + 2 * step)
        next_segment_too_small = len(samples) - segm_end_idx < step
        if next_segment_too_small:
            array = samples[idx:]  # merge this one with next
            yield idx, array
            break
        else:
            array = samples[idx:segm_end_idx]
            yield idx, array


def transcribe_audio_file(asr: SpeechToText, file, step_dur=5, do_cache=False):
    audio = AudioSegment.from_file(
        file,
        target_sr=TARGET_SAMPLE_RATE,
        offset=0.0,
        trim=False,
    )
    step = round(TARGET_SAMPLE_RATE * step_dur)
    arrays = generate_arrays(audio.samples, step)

    cache_file = "aligned_transcripts.pkl"
    if not do_cache or not os.path.isfile(cache_file):

        aligned_transcripts = [
            AlignedTranscript(
                asr.transcribe_audio_array(array, TARGET_SAMPLE_RATE),
                sample_rate=TARGET_SAMPLE_RATE,
                start_idx=idx,
            )
            for idx, array in arrays
        ]
        with open(cache_file, "wb") as f:
            pickle.dump(aligned_transcripts, f)
    else:
        print(f"found cached {cache_file}")

    if do_cache:
        with open(cache_file, "rb") as f:
            aligned_transcripts = pickle.load(f)

    transcript = glue_transcripts(aligned_transcripts)
    return transcript


if __name__ == "__main__":
    """
    python asr_segment_glueing.py facebook/wav2vec2-base-960h
    """
    model = "facebook/wav2vec2-base-960h"
    file = "tests/resources/LibriSpeech_dev-other_116_288046_116-288046-0011.wav"
    asr = SpeechToText(
        model_name=model,
    ).init()
    transcript = transcribe_audio_file(asr, file, step_dur=2, do_cache=True)
    hyp = transcript.text
    ref = next(data_io.read_lines("tests/resources/hyp_stepdur_2.txt"))
    cd = icdiff.ConsoleDiff(cols=120)
    diff_line = "\n".join(
        cd.make_table(
            [ref],
            [hyp],
            "ref",
            "hyp",
        )
    )
    print(diff_line)
    assert hyp == ref
