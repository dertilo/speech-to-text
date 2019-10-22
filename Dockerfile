# Need devel version cause we need /usr/include/cudnn.h
# for compiling libctc_decoder_with_kenlm.so
FROM nvidia/cuda:10.0-cudnn7-devel-ubuntu18.04


# >> START Install base software

# Get basic packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        wget \
        git \
        python3 \
        python3-dev \
        python3-pip \
        python3-wheel \
        python3-numpy \
        libcurl3-dev  \
        ca-certificates \
        gcc \
        sox \
        libsox-fmt-mp3 \
        htop \
        nano \
        swig \
        cmake \
        libboost-all-dev \
        zlib1g-dev \
        libbz2-dev \
        liblzma-dev \
        locales \
        pkg-config \
        libpng-dev \
        libsox-dev \
        libmagic-dev \
        libgsm1-dev \
        libltdl-dev \
        openjdk-8-jdk \
        bash-completion \
        g++ \
        unzip

RUN ln -s -f /usr/bin/python3 /usr/bin/python

# Install NCCL 2.2
RUN apt-get install -qq -y --allow-downgrades --allow-change-held-packages libnccl2=2.3.7-1+cuda10.0 libnccl-dev=2.3.7-1+cuda10.0

# Install Bazel
RUN curl -LO "https://github.com/bazelbuild/bazel/releases/download/0.24.1/bazel_0.24.1-linux-x86_64.deb"
RUN dpkg -i bazel_*.deb

# Install CUDA CLI Tools
RUN apt-get install -qq -y cuda-command-line-tools-10-0

# Install pip
RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

# << END Install base software

RUN pip3 install --upgrade deepspeech-gpu