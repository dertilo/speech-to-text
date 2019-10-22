# speech-to-text

### [m-ailabs-speech-dataset](https://www.caito.de/2019/01/the-m-ailabs-speech-dataset/)

### [DeepSpeech](https://github.com/mozilla/DeepSpeech)
#### docker DeepSpeech
    git clone https://github.com/dertilo/DeepSpeech.git
    docker build -t deepspeech .
#### own docker
    docker build -t stt .
    docker run --shm-size 8G --runtime=nvidia --rm -it -v /home/gunther/tilo_data:/docker-share --env JOBLIB_TEMP_FOLDER=/tmp/ stt:latest bash

#### data-conversion
    docker run --shm-size 8G --runtime=nvidia --rm -it -v /home/gunther/tilo_data:/docker-share --env JOBLIB_TEMP_FOLDER=/tmp/ deepspeech:latest bash
    bin/import_cv2.py --filter_alphabet path/to/some/alphabet.txt /path/to/extracted/language/archive
[datasets](https://voice.mozilla.org/en/datasets)

#### pretrained model
    wget https://github.com/mozilla/DeepSpeech/releases/download/v0.5.1/deepspeech-0.5.1-models.tar.gz
    tar xvfz deepspeech-0.5.1-models.tar.gz
    
##### inference
    MP=/docker-share/data/deepspeech-0.5.1-models && deepspeech --model $MP/output_graph.pbmm --alphabet $MP/alphabet.txt --lm $MP/lm.binary --trie $MP/trie --audio data/smoke_test/LDC93S1.wav