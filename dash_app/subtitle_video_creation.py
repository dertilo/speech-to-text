import json
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
import dash_html_components as html

from dash.dependencies import Input, Output, State

from dash_app.app import app
from dash_app.common import get_store_data
from dash_app.updownload_app import APP_DATA_DIR
from speech_to_text.create_subtitle_files import create_ass_file, SubtitleBlock
import dash_bootstrap_components as dbc
import dash_core_components as dcc


radios_input = dbc.FormGroup(
    [
        dbc.Label("Choose transcripts", html_for="example-radios-row", width=2),
        dbc.Col(
            dcc.Checklist(
                id="transcripts-radio-selection",
            ),
            width=50,
        ),
    ],
    row=True,
)

burn_into_video_form = dbc.Form(
    [
        radios_input,
        dbc.Button(
            "burn into video",
            id="burn-into-video-button",
            n_clicks=0,
            color="primary",
        ),
    ]
)


@app.callback(
    Output("transcripts-radio-selection", "options"),
    Input("transcripts-store", "data"),
)
def update_radio_selection(store_s):
    store_data = get_store_data(store_s)

    options = [{"label": name, "value": name} for name in store_data.keys()]
    return options


@app.callback(
    Output("video-player-subs", "children"),
    Input("burn-into-video-button", "n_clicks"),
    State("subtitle-store", "data"),
    State("transcripts-radio-selection", "value"),
    State("video-file-dropdown", "value"),
)
def burn_into_video_button(n_clicks, store_s, selection, video_file_name):
    video_file = Path(f"{APP_DATA_DIR}/{video_file_name}")
    video_subs_file_name = f"{video_file_name}_subs.mp4"
    subtitle_blocks = [
        SubtitleBlock(**{k: d[k] for k in selection}) for d in json.loads(store_s)
    ]
    with NamedTemporaryFile(suffix=".ass") as f:
        create_ass_file(subtitle_blocks, f.name)
        subprocess.check_output(
            f"/usr/bin/ffmpeg -i {video_file} -vf ass={f.name} {APP_DATA_DIR}/{video_subs_file_name} -y",
            shell=True,
        )
    return [
        html.H5(f"{video_subs_file_name}"),
        html.Video(
            controls=True,
            id="movie_player",
            src=f"/files/{video_subs_file_name}",
            autoPlay=False,
            style={"width": "100%"},
        ),
    ]
