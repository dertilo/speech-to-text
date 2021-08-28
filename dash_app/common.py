import json
from pathlib import Path
from typing import Dict

from dash_app.updownload_app import UPLOAD_DIRECTORY, SUBTITLES_DIR
from speech_to_text.create_subtitle_files import TranslatedTranscript

LANGUAGE_TO_MODELNAME = {
    "spanish": "jonatasgrosman/wav2vec2-large-xlsr-53-spanish",
    "english": "jonatasgrosman/wav2vec2-large-xlsr-53-english",
}


def get_letters_csv(video_file, model_name):
    file = Path(f"{UPLOAD_DIRECTORY}/{video_file}")
    return f"{SUBTITLES_DIR}/{file.stem}_{raw_transcript_name(model_name)}_letters.csv"


def raw_transcript_name(asr_model_name):
    return (
        f"raw-transcript-{asr_model_name}".replace(" ", "")
        .replace("-", "")
        .replace("/", "_")
        .replace(".", "")
    )


def get_store_data(store_s) -> Dict[str, TranslatedTranscript]:
    store_data = json.loads(store_s) if store_s is not None else {}
    store_data = {name: TranslatedTranscript(**d) for name, d in store_data.items()}
    return store_data