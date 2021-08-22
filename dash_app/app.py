import json
import sys
from pprint import pprint

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
    dbc.Row(
        [
            dbc.Col(
                dbc.Button(
                    "create subtitles",
                    id="process-texts-button",
                    n_clicks=0,
                ),
                style={"width": "100%"},
            ),
            dbc.Col(
                dbc.Button(
                    "burn into video",
                    id="process-video-button",
                    n_clicks=0,
                ),
                style={"width": "100%"},
            ),
        ]
    ),
    dbc.Row(
        [
            dbc.Col(id="languages-text-areas"),
            dbc.Col(
                id="subtitles-text-area",
                style={"width": "100%"},
            ),
        ],
    ),
    dbc.Row(
        dbc.Col(
            [
                dbc.Textarea(
                    id="new-transcript-name",
                    value="type some name here",
                    style={"width": "20%", "height": 50},
                ),
                dbc.Button(
                    "create new transcript",
                    id="new-transcript-button",
                    n_clicks=0,
                ),
            ]
        )
    ),
]
app.layout = html.Div(
    [
        dbc.Container(
            page_content,
        ),
        dcc.Store(id="text-areas-data"),
        dcc.Store(id="load-dumped-data-signal"),
    ]
)


@app.callback(
    Output("subtitles-text-area", "children"),
    State("text-areas-data", "data"),
)
def update_subtiles_text_area(n_clicks, data_s):
    if n_clicks > 0:
        data = json.loads(data_s)
        return dbc.Row(
            [
                html.H5("subtitles"),
                dbc.Textarea(
                    id="subtitles",
                    value="\n".join([d["text"] for d in data]),
                    style={"width": "90%", "height": 200*len(data)},
                ),
            ]
        )

    else:
        raise PreventUpdate

@app.callback(
    Output("load-dumped-data-signal", "data"),
    Input("process-texts-button", "n_clicks"),
    State("video-file-dropdown", "value"),
    State({'type': 'transcript-text', 'name': ALL}, 'value'),
    State({'type': 'transcript-text', 'name': ALL}, 'title')
)
def process_button_clicked(n_clicks, video_name,texts,titles):
    if n_clicks > 0:
        assert video_name is not None
        data={title:text for title,text in zip(titles,texts)}
        data_io.write_json(f"{SUBTITLES_DIR}/{video_name}.json", data)
        return "content-of-this-string-does-not-matter"
    else:
        raise PreventUpdate

@app.callback(
    Output("load-dumped-data-signal", "data"),
    Input("new-transcript-button", "n_clicks"),
    State("new-transcript-name", "value"),
    State("video-file-dropdown", "value"),
    State("text-areas-data", "data"),
)
def create_new_text_area(n_clicks, new_transcript_name, video_name, data_s):
    if n_clicks > 0:
        assert video_name is not None
        data = json.loads(data_s) if data_s is not None else []
        data[new_transcript_name]= "enter text here"
        data_io.write_json(f"{SUBTITLES_DIR}/{video_name}.json", data)
        return "content-of-this-string-does-not-matter"
    else:
        raise PreventUpdate


@app.callback(
    Output("text-areas-data", "data"),
    Input("video-file-dropdown", "value"),
    Input("load-dumped-data-signal", "data"),
)
def update_text_area_data(video_name, _):
    return json.dumps(list(data_io.read_jsonl(f"{SUBTITLES_DIR}/{video_name}.jsonl")))


@app.callback(
    Output("languages-text-areas", "children"),
    Input("text-areas-data", "data"),
)
def update_text_areas(data_s: str):
    if data_s is not None:
        data = json.loads(data_s)
        return [
            dbc.Row(
                [
                    html.H5(d["name"]),
                    dbc.Textarea(
                        title=d["name"],
                        id={'type': 'transcript-text', 'name': d["name"]},
                        value=d["text"],
                        style={"width": "90%", "height": 200},
                    ),
                ]
            )
            for k, d in enumerate(data)
        ]
    else:
        raise PreventUpdate


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
