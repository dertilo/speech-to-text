import itertools
import os
from dataclasses import dataclass
from typing import Optional, List, Tuple

import librosa
import numpy as np
import torch
from nemo.collections.asr.parts.preprocessing import AudioSegment
from speech_processing.speech_utils import MAX_16_BIT_PCM
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

TARGET_SAMPLE_RATE = 16_000


@dataclass
class LetterIdx:
    letter: str
    index: int


@dataclass
class AlignedTranscript:
    seq: List[LetterIdx]

    @property
    def text(self):
        return "".join([x.letter for x in self.seq])

    @property
    def array_idx(self):
        return [x.index for x in self.seq]

@dataclass
class GreedyDecoder:
    tgt_dict: List[str]

    def init(self):
        tgt_dict = self.tgt_dict
        self.vocab_size = len(tgt_dict)

        self.blank = (
            tgt_dict.index("<pad>") if "<pad>" in tgt_dict else tgt_dict.index("<s>")
        )
        if "<sep>" in tgt_dict:
            self.silence = tgt_dict.index("<sep>")
        elif "|" in tgt_dict:
            self.silence = tgt_dict.index("|")
        else:
            self.silence = tgt_dict.index("</s>")

        return self

    @property
    def silence_str(self):
        return self.tgt_dict[self.silence]

    def get_prefix(self, idxs):
        """Normalize tokens by handling CTC blank, ASG replabels, etc."""
        idxs = (
            (next(g)[0], k)
            for k, g in itertools.groupby(list(enumerate(idxs)), key=lambda x: x[1])
        )
        seqidx_vocabidx = list(filter(lambda x: x[1] != self.blank, idxs))
        print(f"seqidx_vocabidx: {seqidx_vocabidx}")
        seqidx_vocabidx = self.strip_startend_silence(seqidx_vocabidx)
        print(f"seqidx_vocabidx: {seqidx_vocabidx}")
        prefix_answer = "".join([self.tgt_dict[i] for _, i in seqidx_vocabidx])
        assert not (
            prefix_answer.startswith(self.silence_str)
            or prefix_answer.endswith(self.silence_str)
        )
        seqidx = [i for i, _ in seqidx_vocabidx]
        return {"text": prefix_answer.replace(self.silence_str, " "), "seq_idx": seqidx}

    def strip_startend_silence(self, seqidx_vocabidx):
        while seqidx_vocabidx[0][1] == self.silence:
            seqidx_vocabidx = seqidx_vocabidx[1:]
        while seqidx_vocabidx[-1][1] == self.silence:
            seqidx_vocabidx = seqidx_vocabidx[:-1]
        return seqidx_vocabidx

    def decode(self, emissions):
        B, T, N = emissions.size()
        greedy_path = torch.argmax(emissions, dim=-1)
        return [self.get_prefix(greedy_path[b].tolist()) for b in range(B)]


@dataclass
class SpeechToText:
    model_name: str
    input_sample_rate: Optional[int] = None

    def init(self):
        self.processor = Wav2Vec2Processor.from_pretrained(self.model_name)
        assert self.processor.feature_extractor.do_normalize is True
        self.model = Wav2Vec2ForCTC.from_pretrained(self.model_name)
        assert self.processor.feature_extractor.return_attention_mask == True
        target_dictionary = list(self.processor.tokenizer.get_vocab().keys())
        print(f"target_dictionary: {target_dictionary}")
        self.decoder = GreedyDecoder(target_dictionary).init()
        return self

    def transcribe_audio_array(
        self, audio: np.ndarray, input_sample_rate: Optional[int] = None
    ) -> AlignedTranscript:

        logits = self._calc_logits(audio, input_sample_rate)
        return self.decode_with_timestamps(logits, len(audio))

    def decode_with_timestamps(self, logits, input_len):
        transcript = self.decoder.decode(logits)[0]
        array_idx = [
            round(input_len / logits.size()[1] * i) for i in transcript["seq_idx"]
        ]
        return AlignedTranscript(
            seq=[LetterIdx(l, i) for l, i in zip(transcript["text"], array_idx)]
        )

    def _calc_logits(self, audio: np.ndarray, input_sample_rate: Optional[int] = None):

        input_sample_rate = (
            input_sample_rate
            if input_sample_rate is not None
            else self.input_sample_rate
        )
        assert input_sample_rate is not None

        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / MAX_16_BIT_PCM

        if input_sample_rate != TARGET_SAMPLE_RATE:
            audio = librosa.resample(
                audio.astype(np.float32),
                input_sample_rate,
                TARGET_SAMPLE_RATE,
                scale=True,
            )

        inputs = self.processor(
            audio,
            sampling_rate=TARGET_SAMPLE_RATE,
            return_tensors="pt",
            # return_attention_mask=True,
        )
        with torch.no_grad():
            logits = self.model(
                inputs.input_values, attention_mask=inputs.attention_mask
            ).logits
        return logits


if __name__ == "__main__":
    # idxs = list((k,list(g)) for k,g in itertools.groupby(list(enumerate("thisss isss a ttteeest")), key=lambda x: x[1]))
    # print(idxs)
    audio = AudioSegment.from_file(
        "/home/tilo/data/asr_data/GERMAN/tuda/raw/german-speechdata-package-v2/dev/2015-02-09-15-18-46_Samson.wav",
        target_sr=TARGET_SAMPLE_RATE,
        offset=0.0,
        trim=False,
    )

    asr = SpeechToText(
        model_name="jonatasgrosman/wav2vec2-large-xlsr-53-german",
    ).init()
    array = audio.samples
    print(f"array-shape: {array.shape}")
    logits_file = "/tmp/logits.npy"
    if not os.path.isfile(logits_file):
        assert False
        logits = asr._calc_logits(array, audio.sample_rate)
        np.save(logits_file, logits)
    logits = torch.from_numpy(np.load(logits_file))
    print(asr.decode_with_timestamps(logits, len(array)))
    # print(asr.transcribe_audio_array(array, audio.sample_rate))
