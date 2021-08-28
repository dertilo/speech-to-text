from dash.dependencies import Input, Output, State

from dash_app.app import app
from dash_app.common import get_store_data
from speech_to_text.create_subtitle_files import create_ass_file
import dash_bootstrap_components as dbc


radios_input = dbc.FormGroup(
    [
        dbc.Label("Radios", html_for="example-radios-row", width=2),
        dbc.Col(
            dbc.RadioItems(
                id="transcripts-radio-selection",
            ),
            width=10,
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

# @app.callback(
#     Output("transcripts-radio-selection", "options"),
#     Input("burn-into-video-button", "n_clicks"),
# )
# def burn_into_video_button(store_s):
#     store_data = get_store_data(store_s)
#
#     options = [{"label": name, "value": name} for name in store_data.keys()]
#     return options


# create_ass_file()
# subprocess.check_output(
#     f"/usr/bin/ffmpeg -i {video_file} -vf ass={name2subfile[video_file.stem]} {video_file.stem}_sub.mp4 -y",
#     shell=True,
# )
