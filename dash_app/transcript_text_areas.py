import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Dict

import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate
from util import data_io

from dash_app.app import app
from dash_app.updownload_app import UPLOAD_DIRECTORY, SUBTITLES_DIR
from speech_to_text.create_subtitle_files import TranslatedTranscript
from speech_to_text.subtitle_creation import convert_to_wav_transcribe
from speech_to_text.transcribe_audio import SpeechToText

NO_NAME = "enter some name here"
LANGUAGE_TO_MODELNAME = {
    "spanish": "jonatasgrosman/wav2vec2-large-xlsr-53-spanish",
    "english": "jonatasgrosman/wav2vec2-large-xlsr-53-english",
}

new_text_area_form = dbc.Form(
    [
        dbc.FormGroup(
            [
                dbc.Label("Name", className="mr-2"),
                dbc.Input(type="name", id="new-transcript-name", placeholder=NO_NAME),
            ],
            className="mr-3",
        ),
        dbc.Button("create new transcript", id="new-transcript-button"),
    ],
    inline=True,
)


def create_raw_transcript(video_file, model_name):
    file = Path(f"{UPLOAD_DIRECTORY}/{video_file}")
    raw_transcript_file = (
        f"{SUBTITLES_DIR}/{file.stem}_{raw_transcript_name(model_name)}.txt"
    )
    if not os.path.isfile(raw_transcript_file):
        asr = SpeechToText(
            model_name=model_name,
        ).init()
        transcript = convert_to_wav_transcribe(asr, str(file))
        data_io.write_lines(
            f"{SUBTITLES_DIR}/{file.stem}_{raw_transcript_name(model_name)}_letters.csv",
            [f"{l.letter}\t{l.index}" for l in transcript.letters],
        )

        raw_transcript = "".join([l.letter for l in transcript.letters])
        data_io.write_lines(
            raw_transcript_file,
            [raw_transcript],
        )
    else:
        raw_transcript = list(data_io.read_lines(raw_transcript_file))[0]
    return raw_transcript


def raw_transcript_name(asr_model_name):
    return (
        f"raw-transcript-{asr_model_name}".replace(" ", "")
        .replace("-", "")
        .replace(".", "")
    )


@app.callback(
    Output("raw-transcript", "children"),
    Input("create-raw-transcripts-button", "n_clicks"),
    Input("transcripts-store", "data"),
    State("video-file-dropdown", "value"),
    State("asr-model-dropdown", "value"),
)
def calc_raw_transcript(n_clicks, store_s, video_file, asr_model):
    store_data = get_store_data(store_s)
    rtm = raw_transcript_name(asr_model)
    if n_clicks > 0 and rtm not in store_data:
        raw_transcript = create_raw_transcript(video_file, asr_model)
        return [raw_transcript]
    elif rtm in store_data:
        return [store_data[rtm].text]
    else:
        raise PreventUpdate


@app.callback(
    Output("languages-text-areas", "children"),
    Input("transcripts-store", "data"),
    Input("new-transcript-button", "n_clicks"),
    State("new-transcript-name", "value"),
    State("asr-model-dropdown", "value"),
)
def update_text_areas(store_s: str, n_clicks, new_name, asr_model):
    store_data = get_store_data(store_s)
    print(f"store-data: {[asdict(v) for v in store_data.values()]}")
    transcripts = list(store_data.values())
    if new_name is not None and new_name != NO_NAME:
        transcripts.append(
            TranslatedTranscript(
                raw_transcript_name(asr_model), len(transcripts), "enter text here"
            )
        )

    rows = []
    for sd in sorted(transcripts, key=lambda x: x.order):
        rows.append(dbc.Row(html.H5(sd.name)))
        rows.append(
            dbc.Row(
                dbc.Textarea(
                    title=sd.name,
                    id={"type": "transcript-text", "name": sd.name},
                    value=sd.text,
                    style={"width": "90%", "height": 200, "fontSize": 11},
                )
            )
        )
    return rows


def get_store_data(store_s) -> Dict[str, TranslatedTranscript]:
    store_data = json.loads(store_s) if store_s is not None else {}
    store_data = {name: TranslatedTranscript(**d) for name, d in store_data.items()}
    return store_data
