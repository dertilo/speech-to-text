import subprocess
import sys
sys.path.append(".")
from pathlib import Path

from speech_to_text.create_subtitle_files import create_subtitles

if __name__ == "__main__":

    video_dir = sys.argv[1]
    transript_dir = sys.argv[2]
    manual_transcripts_dir = sys.argv[3]
    name2subfile = {
        p.stem: str(p) for p in create_subtitles(transript_dir, manual_transcripts_dir)
    }

    for video_file in Path(video_dir).glob("*.*"):
        subprocess.check_output(
            f"/usr/bin/ffmpeg -i {video_file} -vf ass={name2subfile[video_file.stem]} {video_file.stem}_sub.mp4 -y",
            shell=True,
        )
