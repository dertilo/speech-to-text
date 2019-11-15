
### docker container
`docker run --runtime=nvidia --rm -it --ipc=host --name w2l -v /home/gunther/tilo_data:/docker-share wav2letter/wav2letter:cuda-latest bash`
`pip install sentencepiece==0.1.82`

### preprocess librispeech + train sentencepiece

    cd wav2letter/recipes/models/seq2seq_tds/librispeech
    python3 prepare.py

make test in /root/wav2letter/build is failing in one test
