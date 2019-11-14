from util import data_io

from pathlib import Path
home = str(Path.home())


if __name__ == '__main__':
    base_url = 'http://www.openslr.org/resources/12'
    files = ['dev-clean.tar.gz','train-clean-100.tar.gz','test-clean.tar.gz']
    data_folder = home+'/data/libri-speech'
    [data_io.download_data(base_url,file_name,data_folder,unzip_it=True) for file_name in files]