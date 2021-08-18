import os
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    os.makedirs(output_dir)

    for input_file in Path(input_dir).glob("*.*"):  # mp4, m4a
        command = f"ffmpeg -y -i '{input_file}' -ab 160k -ac 1 -ar 16000 -vn {output_dir}/{input_file.stem}.wav"  #
        subprocess.call(command, shell=True)
