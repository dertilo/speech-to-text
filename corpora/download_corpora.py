import os

from util import data_io


def download_librispeech_en(path):
    base_url = "http://www.openslr.org/resources/12"
    files = ["dev-clean.tar.gz", "train-clean-100.tar.gz", "test-clean.tar.gz"]
    [
        data_io.download_data(
            base_url,
            file_name,
            os.path.join(path, "libri-speech"),
            unzip_it=True,
            verbose=True,
        )
        for file_name in files
    ]


def download_spanish_srl_corpora(path):
    """
    all together 18698 utterances
    :return:
    """
    dsnumer_abbrev = [
        ("71", "cl"),  # chilean
        ("72", "co"),  # colombian
        ("73", "pe"),  # peruvian
        ("74", "pr"),  # puerto rico
        ("75", "ve"),  # venezuelan
    ]
    path = os.path.join(path, "openslr_spanish")
    for dsnumber, abbrev in dsnumer_abbrev:
        for sex in ["male", "female"]:
            data_io.download_data(
                "https://www.openslr.org/resources/%s" % dsnumber,
                "es_%s_%s.zip" % (abbrev, sex),
                os.path.join(path, "es_%s_%s" % (abbrev, sex)),
                unzip_it=True,
                do_raise=False,
                verbose=True,
            )


def download_mailabs_corpus(path, file="es_ES.tgz"):
    url = "http://www.caito.de/data/Training/stt_tts"
    data_folder = os.path.join(path, "m-ailabs_es")
    data_io.download_data(
        url, file, data_folder, unzip_it=True, verbose=True,
    )


def download_herioco_umsa(path):
    url = "http://www.openslr.org/resources/39"
    data_folder = os.path.join(path, "LDC2006S37")
    data_io.download_data(
        url, "LDC2006S37.tar.gz", data_folder, verbose=True, unzip_it=True,
    )


if __name__ == "__main__":
    path = os.path.join(os.environ["HOME"], "data/asr_data")
    download_herioco_umsa(path)
    # download_librispeech_en()
    download_mailabs_corpus(path)
    download_spanish_srl_corpora(path)
