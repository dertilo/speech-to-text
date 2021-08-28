import json
import os
import sys
from pprint import pprint

import dash_table
from dash.exceptions import PreventUpdate

sys.path.append(".")
from pathlib import Path

import dash
from dash.dependencies import Input, Output, State, ALL
import dash_core_components as dcc
import dash_html_components as html
from flask import Flask, send_from_directory
import dash_bootstrap_components as dbc
import dash_auth
from util import data_io

from dash_app.updownload_app import (
    save_file,
    uploaded_files,
    UPLOAD_DIRECTORY,
    SUBTITLES_DIR,
)

VALID_USERNAME_PASSWORD_PAIRS = {
    d["login"]: d["password"] for d in data_io.read_jsonl("credentials.jsonl")
}


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
        dbc.Button(
            "create new transcript", id="new-transcript-button"
        ),
    ],
    inline=True,
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
    html.H2("transcript alignment"),
    dbc.Row(
        [
            dbc.Col(
                dbc.Button(
                    "create subtitles",
                    id="process-texts-button",
                    n_clicks=0,
                    color="primary",
                ),
                style={"width": "100%"},
            ),
            dbc.Col(
                dbc.Button(
                    "burn into video",
                    id="process-video-button",
                    n_clicks=0,
                    color="primary",
                ),
                style={"width": "100%"},
            ),
        ]
    ),
    # dbc.Row(dbc.Col(html.Div(" "))),
    dbc.Row(
        [
            dbc.Col(id="languages-text-areas"),
            dbc.Col(
                id="subtitles-text-area",
                style={"width": "100%"},
            ),
        ],
        style={"padding-top": 20},
    ),
    dbc.Row(
        new_text_area_form,
        style={"padding-top": 20},
    ),
]
app.layout = html.Div(
    [
        dbc.Container(
            page_content,
        ),
        dcc.Store(id="transcripts-store"),
        dcc.Store(id="load-dumped-data-signal"),
    ]
)


@app.callback(
    Output("load-dumped-data-signal", "data"),
    Output("subtitles-text-area", "children"),
    Input("process-texts-button", "n_clicks"),
    State("video-file-dropdown", "value"),
    State({"type": "transcript-text", "name": ALL}, "value"),
    State({"type": "transcript-text", "name": ALL}, "title"),
)
def dump_to_disk_process_subtitles(n_clicks, video_name, texts, titles):
    if n_clicks > 0:
        assert video_name is not None
        data = {title: text for title, text in zip(titles, texts)}
        data_io.write_json(f"{SUBTITLES_DIR}/{video_name}.json", data)

        subtitles = dbc.Row(
            [
                html.H5("subtitles"),
                dash_table.DataTable(
                    columns=[{"id": cn, "name": cn} for cn in ["start-time"] + titles],
                    data=[dict({t: i for t in titles}) for i in range(0, 100)],
                    style_table={"height": 500, "overflowY": "scroll", "width": 400},
                ),
            ]
        )
        return "content-of-this-string-does-not-matter", subtitles
    else:
        raise PreventUpdate


@app.callback(
    Output("transcripts-store", "data"),
    Input("video-file-dropdown", "value"),
    Input("load-dumped-data-signal", "data"),
)
def update_store_data(video_name, _):
    if os.path.isfile(f"{SUBTITLES_DIR}/{video_name}.json"):
        print("update_store_data")
        return json.dumps(data_io.read_json(f"{SUBTITLES_DIR}/{video_name}.json"))
    else:
        print(f"not updated update_store_data")
        raise PreventUpdate


@app.callback(
    Output("languages-text-areas", "children"),
    Input("transcripts-store", "data"),
    Input("new-transcript-button", "n_clicks"),
    State("new-transcript-name", "value"),
)
def update_text_areas(store_s: str, n_clicks, new_name):
    store_data = json.loads(store_s) if store_s is not None else {}
    print(store_data)
    if new_name is not None and new_name != NO_NAME:
        store_data[new_name] = "enter text here"
    return [
        dbc.Row(
            [
                html.H5(name),
                dbc.Textarea(
                    title=name,
                    id={"type": "transcript-text", "name": name},
                    value=text,
                    style={"width": "90%", "height": 200},
                ),
            ]
        )
        for k, (name, text) in enumerate(store_data.items())
    ]


# dbc.Col(
#     [
#         html.H5(f"processed {name}"),
#         dbc.Textarea(
#             id=f"processed-text-{k}",
#             style={"width": "100%", "height": 200},
#         ),
#     ]
# ),


@app.callback(
    Output("video-file-dropdown", "options"),
    Output("video-file-dropdown", "value"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
)
def update_output(contents, names, dates):
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


if __name__ == "__main__":
    app.run_server(debug=True)
