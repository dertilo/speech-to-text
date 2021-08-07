import itertools
from dataclasses import dataclass
from typing import Optional, List

import librosa
import numpy as np
import torch
from nemo.collections.asr.parts.preprocessing import AudioSegment
from speech_processing.speech_utils import MAX_16_BIT_PCM
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

TARGET_SAMPLE_RATE = 16_000


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

    def get_prefix(self, idxs):
        """Normalize tokens by handling CTC blank, ASG replabels, etc."""
        idxs = (g[0] for g in itertools.groupby(idxs))
        idxs = filter(lambda x: x != self.blank, idxs)
        prefix_answer = ""
        for i in list(idxs):
            prefix_answer += self.tgt_dict[i]
        return prefix_answer.replace("|", " ").strip()

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
    ) -> str:
        logits = self._calc_logits(audio, input_sample_rate)
        transcript = self.decoder.decode(logits)[0]
        return transcript

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
    audio = AudioSegment.from_file(
        "/home/tilo/data/asr_data/GERMAN/tuda/raw/german-speechdata-package-v2/dev/2015-02-09-15-18-46_Samson.wav",
        target_sr=TARGET_SAMPLE_RATE,
        offset=0.0,
        trim=False,
    )

    asr = SpeechToText(
        model_name="jonatasgrosman/wav2vec2-large-xlsr-53-german",
    ).init()
    print(asr.transcribe_audio_array(audio.samples, audio.sample_rate))
