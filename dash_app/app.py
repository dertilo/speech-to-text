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

from dash_app.updownload_app import save_file, uploaded_files, UPLOAD_DIRECTORY

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

server = Flask(__name__)
app = dash.Dash(__name__,server=server, external_stylesheets=external_stylesheets)


@server.route("/download/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=True)

@server.route("/files/<path:path>")
def serve_static(path):
    return send_from_directory(UPLOAD_DIRECTORY, path,as_attachment=False)

app.layout = html.Div(
    [
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
        ),
        html.Div(
            id="output-data-upload",
            children=[
                html.Label(
                    ["Single dynamic Dropdown", dcc.Dropdown(id="my-dynamic-dropdown")]
                )
            ],
        ),
        html.Div(
            id="video-player"
        ),
    ]
)

@app.callback(
    Output("my-dynamic-dropdown", "options"),
    Output("my-dynamic-dropdown", "value"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
)
def update_output(contents, names, list_of_dates):
    if contents is not None:
        for name, data in zip(names, contents):
            save_file(name, data)
    options = [{"label": Path(f).stem, "value": f} for f in uploaded_files()]
    return options, options[0]["value"]


@app.callback(
    Output("video-player", "children"),
    Input("my-dynamic-dropdown", "value"),
)
def update_video_player(file):
    return html.Div(
       children=[
           html.Video(
               controls=True,
               id="movie_player",
               src=f"/files/{file}",
               autoPlay=True
           ),
       ]
   )


if __name__ == "__main__":
    app.run_server(debug=True)
