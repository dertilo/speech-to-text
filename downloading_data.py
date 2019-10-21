from util import data_io

if __name__ == '__main__':
    # file_name = 'es_ES.tgz'
    file_name = 'de_DE.tgz'
    download_path = '/docker-share/data/m-ailabs-speech-dataset'
    data_io.download_data('http://www.caito.de/data/Training/stt_tts', file_name=file_name, data_folder=download_path, verbose=True)