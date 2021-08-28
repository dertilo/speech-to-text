from dataclasses import asdict
from datetime import timedelta
from pathlib import Path

import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
from dash.dependencies import Output, Input, State, ALL
from dash.exceptions import PreventUpdate
from util import data_io

from dash_app.app import app
from dash_app.common import get_letters_csv, raw_transcript_name
from dash_app.updownload_app import SUBTITLES_DIR
from speech_to_text.create_subtitle_files import (
    TranslatedTranscript,
    segment_transcript_to_subtitle_blocks,
)
from speech_to_text.transcribe_audio import TARGET_SAMPLE_RATE

process_button = dbc.Button(
    "create subtitles",
    id="process-texts-button",
    n_clicks=0,
    color="primary",
)

def build_json_name(video_file,model_name):
    return f"{SUBTITLES_DIR}/{Path(video_file).stem}_{raw_transcript_name(model_name)}.json"

@app.callback(
    Output("load-dumped-data-signal", "data"),
    Output("subtitles-text-area", "children"),
    Input("process-texts-button", "n_clicks"),
    State("video-file-dropdown", "value"),
    State({"type": "transcript-text", "name": ALL}, "value"),
    State({"type": "transcript-text", "name": ALL}, "title"),
    State("asr-model-dropdown", "value"),
)
def dump_to_disk_process_subtitles(n_clicks, video_file, texts, titles,model_name):
    if n_clicks > 0:
        assert video_file is not None
        data = {
            title: TranslatedTranscript(title, k, text)
            for k, (title, text) in enumerate(zip(titles, texts))
        }
        data_io.write_json(
            build_json_name(video_file,model_name),
            {name: asdict(v) for name, v in data.items()},
        )

        named_blocks = segment_transcript_to_subtitle_blocks(
            get_letters_csv(video_file,model_name), list(data.values())
        )
        subtitles = dbc.Row(
            [
                dash_table.DataTable(
                    columns=[{"id": cn, "name": cn} for cn in ["start-time"] + titles],
                    data=[
                        {
                            **{
                                name: "".join([l.letter for l in b[name]])
                                for name in titles
                            },
                            **{
                                "start-time": str(
                                    timedelta(
                                        milliseconds=round(
                                            1000
                                            * b[titles[0]][0].index
                                            / TARGET_SAMPLE_RATE
                                        )
                                    )
                                )
                            },
                        }
                        for b in named_blocks
                    ],
                    style_table={
                        "height": 200 * len(titles),
                        "overflowY": "scroll",
                        "width": "100%",
                        "font-size": 9,
                    },
                    style_cell={
                        # "overflow": "hidden",
                        # "textOverflow": "ellipsis",
                        # "maxWidth": 0,
                        "textAlign": "left",
                        "height": "auto",
                    },
                ),
            ],
            style={"width": "100%"},
        )
        return "content-of-this-string-does-not-matter", [
            html.H5("segmentation"),
            subtitles,
        ]
    else:
        raise PreventUpdate
