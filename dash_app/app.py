import base64
import datetime
import io
import os
from pathlib import Path

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from flask import Flask, send_from_directory
import dash_bootstrap_components as dbc
import dash_auth
from util import data_io

from dash_app.updownload_app import save_file, uploaded_files, UPLOAD_DIRECTORY
VALID_USERNAME_PASSWORD_PAIRS = {d["login"]:d["password"] for d in data_io.read_jsonl("credentials.jsonl")}


server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

@server.route("/download/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=True)


@server.route("/files/<path:path>")
def serve_static(path):
    return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=False)


video_selection_upload = dbc.Row(
    [
        dbc.Col(
            html.Div(
                id="output-data-upload",
                children=[
                    html.Label(
                        [
                            "video-files",
                            dcc.Dropdown(id="my-dynamic-dropdown"),
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
text_areas = dbc.Row(
    [
        dbc.Col(
            html.Div(
                [
                    html.H5("raw text"),
                    dbc.Textarea(
                        id="raw-text",
                        value="Textarea content initialized\nwith multiple lines of text",
                        style={"width": "100%", "height": 200},
                    ),
                    dbc.Button(
                        "save & submit",
                        id="raw-text-button",
                        n_clicks=0,
                    ),
                ]
            )
        ),
        dbc.Col(
            [
                html.H5("processed text"),
                dbc.Textarea(
                    id="processed-text",
                    style={"width": "100%", "height": 200},
                ),
            ]
        ),
    ]
)
page_content = [
    html.H2("subtitles creator"),
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
    text_areas,
]
app.layout = html.Div(
    [
        dbc.Container(
            page_content,
        ),
        dcc.Store(id="current-experiment"),
    ]
)


@app.callback(
    Output("processed-text", "value"),
    Input("raw-text-button", "n_clicks"),
    State("raw-text", "value"),
)
def process_text(n_clicks, raw_text):
    return raw_text.upper()


@app.callback(
    Output("my-dynamic-dropdown", "options"),
    Output("my-dynamic-dropdown", "value"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
)
def update_output(contents, names, dates):
    if contents is not None:
        for name, data, date in zip(names, contents, dates):
            save_file(name, data, date)
    options = [{"label": Path(f).stem, "value": f} for f in uploaded_files()]
    return options, options[0]["value"]


@app.callback(
    Output("video-player", "children"),
    Input("my-dynamic-dropdown", "value"),
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


if __name__ == "__main__":
    app.run_server(debug=True)
