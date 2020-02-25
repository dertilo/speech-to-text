import subprocess

if __name__ == "__main__":
    augmented_filename = "/tmp/augmented.wav"
    tempo = 1.1
    gain = 0
    sox_augment_params = [
        "tempo",
        "{:.3f}".format(tempo),
        "gain",
        "{:.3f}".format(gain),
    ]
    noise_gain = -16
    # sox original.wav -p gain -16 | sox -m - <(sox original.wav -p synth brownnoise vol 0.8) addednoise.wav
    # subprocess.call(['bash', '-c','sox /tmp/original.wav -p gain -1 | sox -m - <(sox /tmp/original.wav -p synth brownnoise vol 0.8) /tmp/addednoise.wav'])
    sox_params = 'sox {original} -p gain {original_gain} | sox -m - <(sox {original} -p synth brownnoise gain {noise_gain}) {augmented_file} {params} >/dev/null 2>&1'.format(
        original='/tmp/original.wav',original_gain=gain,noise_gain=noise_gain,augmented_file = augmented_filename, params=" ".join(sox_augment_params)
    )
    subprocess.call(['bash','-c',sox_params])
