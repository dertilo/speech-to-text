import sys

sys.path.append(".")
import difflib
from typing import Optional, List, Tuple

import numpy as np
from nemo.collections.asr.parts.preprocessing import AudioSegment

from speech_to_text.transcribe_audio import SpeechToText, AlignedTranscript, LetterIdx

TARGET_SAMPLE_RATE = 16_000


def glue_transcripts(
    aligned_transcripts: List[Tuple[int, AlignedTranscript]],
    step=round(TARGET_SAMPLE_RATE * 2),
    debug=False,
):
    all_but_last_must_be_of_same_len = (
        len(set((len(x.seq) for _, x in aligned_transcripts[:-1]))) == 1
    ), [len(x.seq) for _, x in aligned_transcripts]
    assert all_but_last_must_be_of_same_len

    previous: Optional[AlignedTranscript] = None
    letters: List[LetterIdx] = []
    for idx, ts in aligned_transcripts:
        if previous is not None:
            right = AlignedTranscript(seq=[s for s in ts.seq if s.index < step])
            left = AlignedTranscript(seq=[s for s in previous.seq if s.index >= step])
            sm.set_seqs(left.text, right.text)
            matches = [m for m in sm.get_matching_blocks() if m.size > 0]
            aligned_idx = [(m.a + k, m.b + k) for m in matches for k in range(m.size)]
            match_idx = np.argmin(
                [np.abs(i - round(len(left.text) / 2)) for i, _ in aligned_idx]
            )
            glue_left, glue_right = aligned_idx[match_idx]
            glue_idx_left = left.seq[glue_left].index
            glue_idx_right = right.seq[glue_right].index
            letters_right = [
                LetterIdx(x.letter, x.index + idx)
                for x in right.seq
                if x.index > glue_idx_right
            ]
            letters_left = [
                LetterIdx(x.letter, x.index + idx - step)
                for x in left.seq
                if x.index <= glue_idx_left
            ]
            letters.extend(letters_left)
            letters.extend(letters_right)
            if debug:
                print(f"left: {left.text}, right: {right.text}")
                print(
                    f"GLUED left: {AlignedTranscript(letters_left).text}, right: {AlignedTranscript(letters_right).text}"
                )
        else:
            right = AlignedTranscript(seq=[s for s in ts.seq if s.index < step])
            if debug:
                print(f"initial: {right.text}")
            assert idx == 0
            letters.extend([x for x in right.seq])
        previous = ts

    transcript = AlignedTranscript(seq=letters)
    return transcript


def generate_arrays(samples: np.ndarray):
    for idx in range(0, len(samples), step):
        segm_end_idx = round(idx + 2 * step)
        next_segment_too_small = len(samples) - segm_end_idx < step
        if next_segment_too_small:
            array = samples[idx:]  # merge this one with next
        else:
            array = samples[idx:segm_end_idx]

        if len(array) >= step:
            yield idx, array
        else:
            break


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
    sample_rate = audio.sample_rate
    step = round(TARGET_SAMPLE_RATE * 2)

    arrays = generate_arrays(audio.samples)
    aligned_transcripts = [
        (idx, asr.transcribe_audio_array(array, sample_rate)) for idx, array in arrays
    ]
    transcript = glue_transcripts(aligned_transcripts, step=step)
    print(transcript.text)
