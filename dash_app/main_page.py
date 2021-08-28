import json
import os
from pathlib import Path

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate
from util import data_io

from dash_app.app import app
from dash_app.subtitle_video_creation import burn_into_video_form
from dash_app.common import LANGUAGE_TO_MODELNAME, build_json_name
from dash_app.transcript_text_areas import transcribe_button
from dash_app.updownload_app import (
    save_file,
    uploaded_files,
    UPLOAD_DIRECTORY,
)

video_selection_upload = dbc.Row(
    [
        dbc.Col(
            html.Div(
                id="output-data-upload",
                children=[
                    html.Label(
                        [
                            "video-files",
                            dcc.Dropdown(id="video-file-dropdown"),
                        ],
                        style={"width": "100%"},
                    )
                ],
            )
        ),
        dbc.Col(
            dcc.Upload(
                id="upload-data",
                children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
                style={
                    "width": "100%",
                    "height": "60px",
                    "lineHeight": "60px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px",
                },
                # Allow multiple files to be uploaded
                multiple=True,
            )
        ),
    ]
)
page_content = [
    html.H1("subtitles creator"),
    html.H5("select video-file in dropdown, if not there upload it!"),
    video_selection_upload,
    dbc.Row(
        [
            dbc.Col(
                html.Div(id="video-player"),
            ),
            dbc.Col(html.Div(id="video-player-subs")),
        ]
    ),
    dbc.Row(
        [
            dbc.Col(
                [
                    html.Label("language"),
                    dcc.Dropdown(
                        id="asr-model-dropdown",
                        options=[
                            {"label": k, "value": v}
                            for k, v in LANGUAGE_TO_MODELNAME.items()
                        ],
                        value=LANGUAGE_TO_MODELNAME["spanish"],
                    ),
                ]
            ),
            dbc.Col(
                transcribe_button,
                style={"width": "100%", "padding-top": 40},
            ),
            dbc.Col(
                burn_into_video_form,
                style={"width": "100%"},
            ),
        ]
    ),
    dbc.Spinner(html.Div(id="raw-transcript", style={"fontSize": 10})),
    html.Div(id="dependent_on_raw_transcript")
]


@app.callback(
    Output("transcripts-store", "data"),
    Input("video-file-dropdown", "value"),
    Input("load-dumped-data-signal", "data"),
    State("asr-model-dropdown", "value"),

)
def update_store_data(video_file, _,model_name):
    if os.path.isfile(build_json_name(video_file,model_name)):
        return json.dumps(
            data_io.read_json(build_json_name(video_file,model_name))
        )
    else:
        raise PreventUpdate


@app.callback(
    Output("video-file-dropdown", "options"),
    Output("video-file-dropdown", "value"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
)
def update_video_file_dropdown(contents, names, dates):
    if contents is not None:
        for name, data, date in zip(names, contents, dates):
            save_file(name, data, date)
    options = [{"label": Path(f).stem, "value": f} for f in uploaded_files()]
    return options, options[0]["value"] if len(options) > 0 else None


@app.callback(
    Output("video-player", "children"),
    Input("video-file-dropdown", "value"),
)
def update_video_player(file):
    fullfile = f"{UPLOAD_DIRECTORY}/{file}"
    return [
        html.H5(f"{Path(fullfile).name}"),
        html.Video(
            controls=True,
            id="movie_player",
            src=f"/files/{file}",
            autoPlay=False,
            style={"width": "100%"},
        ),
    ]
