import sys

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
    aligned_transcripts: List[Tuple[int, AlignedTranscript]],
    step=round(TARGET_SAMPLE_RATE * 2),
    debug=True,
) -> AlignedTranscript:
    all_but_last_must_be_of_same_len = (
        len(set((len(x.letters) for _, x in aligned_transcripts[:-1]))) == 1
    ), [len(x.letters) for _, x in aligned_transcripts]
    assert all_but_last_must_be_of_same_len

    sm = difflib.SequenceMatcher()
    sample_rate = None
    previous: Optional[AlignedTranscript] = None
    letters: List[LetterIdx] = []
    for idx, ts in aligned_transcripts:
        if sample_rate is None:
            sample_rate = ts.sample_rate
        if previous is not None:
            right = AlignedTranscript(
                letters=[s for s in ts.letters if s.index < step],
                sample_rate=ts.sample_rate,
            )
            left = AlignedTranscript(
                letters=[s for s in previous.letters if s.index >= step],
                sample_rate=ts.sample_rate,
            )
            sm.set_seqs(left.text, right.text)
            matches = [m for m in sm.get_matching_blocks() if m.size > 0]
            aligned_idx = [(m.a + k, m.b + k) for m in matches for k in range(m.size)]
            match_idx = np.argmin(
                [np.abs(i - round(len(left.text) / 2)) for i, _ in aligned_idx]
            )
            glue_left, glue_right = aligned_idx[match_idx]
            glue_idx_left = left.letters[glue_left].index
            glue_idx_right = right.letters[glue_right].index
            letters_right = [
                LetterIdx(x.letter, x.index + idx)
                for x in right.letters
                if x.index > glue_idx_right
            ]
            letters_left = [
                LetterIdx(x.letter, x.index + idx - step)
                for x in left.letters
                if x.index <= glue_idx_left
            ]
            letters.extend(letters_left)
            letters.extend(letters_right)
            if debug:
                print(f"left: {left.text}, right: {right.text}")
                print(
                    f"GLUED left: {AlignedTranscript(letters_left,ts.sample_rate).text}, right: {AlignedTranscript(letters_right,ts.sample_rate).text}"
                )
        else:
            right = AlignedTranscript(
                [s for s in ts.letters if s.index < step], ts.sample_rate
            )
            if debug:
                print(f"initial: {right.text}")
            assert idx == 0
            letters.extend([x for x in right.letters])
        previous = ts

    letters.extend([LetterIdx(s.letter, s.index + idx) for s in previous.letters if s.index >= step])
    assert all((letters[k].index>letters[k-1].index for k in range(1,len(letters))))
    transcript = AlignedTranscript(letters, sample_rate)
    return transcript


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


def transcribe_audio_file(asr: SpeechToText, file, step_dur=10):  # seconds
    audio = AudioSegment.from_file(
        file,
        target_sr=TARGET_SAMPLE_RATE,
        offset=0.0,
        trim=False,
    )
    step = round(TARGET_SAMPLE_RATE * step_dur)
    arrays = generate_arrays(audio.samples, step)
    aligned_transcripts = [
        (idx, asr.transcribe_audio_array(array, TARGET_SAMPLE_RATE))
        for idx, array in arrays
    ]
    transcript = glue_transcripts(aligned_transcripts, step=step)
    return transcript


if __name__ == "__main__":
    model = sys.argv[1]
    file = sys.argv[2]
    asr = SpeechToText(
        model_name=model,
    ).init()
    transcript = transcribe_audio_file(asr, file)
    print(transcript.text)
