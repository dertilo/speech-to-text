import json
import os
from dataclasses import asdict
from pathlib import Path

import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Output, Input, State
from util import data_io

from dash_app.app import app
from dash_app.updownload_app import UPLOAD_DIRECTORY, SUBTITLES_DIR
from speech_to_text.create_subtitle_files import TranslatedTranscript
from speech_to_text.subtitle_creation import convert_to_wav_transcribe
from speech_to_text.transcribe_audio import SpeechToText

NO_NAME = "enter some name here"

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


def create_raw_transcript(video_file):
    file = Path(f"{UPLOAD_DIRECTORY}/{video_file}")
    raw_transcript_file = f"{SUBTITLES_DIR}/{file.stem}_raw_transcript.txt"
    if not os.path.isfile(raw_transcript_file):
        asr = SpeechToText(
            model_name="jonatasgrosman/wav2vec2-large-xlsr-53-spanish",
        ).init()
        transcript = convert_to_wav_transcribe(asr, str(file))
        data_io.write_lines(
            f"{SUBTITLES_DIR}/{file.stem}_letters.csv",
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


@app.callback(
    Output("raw-transcript", "children"),
    Output("languages-text-areas", "children"),
    Input("transcripts-store", "data"),
    Input("new-transcript-button", "n_clicks"),
    State("video-file-dropdown", "value"),
    State("new-transcript-name", "value"),
)
def update_text_areas(store_s: str, n_clicks, video_file, new_name):
    store_data = json.loads(store_s) if store_s is not None else {}
    store_data = {name: TranslatedTranscript(**d) for name, d in store_data.items()}
    print(f"store-data: {[asdict(v) for v in store_data.values()]}")
    if "raw-transcript" not in store_data:
        raw_transcript = create_raw_transcript(video_file)
        store_data["raw-transcript"] = TranslatedTranscript(
            "raw-transcript", 0, raw_transcript
        )

    if new_name is not None and new_name != NO_NAME:
        store_data[new_name] = TranslatedTranscript(
            "raw-transcript", len(store_data.keys()), "enter text here"
        )

    return [store_data["raw-transcript"].text], [
        dbc.Row(
            [
                html.H5(name),
                dbc.Textarea(
                    title=name,
                    id={"type": "transcript-text", "name": name},
                    value=sd.text,
                    style={"width": "90%", "height": 200, "fontSize": 11},
                ),
            ]
        )
        for name, sd in sorted(store_data.items(), key=lambda x: x[1].order)
    ]
