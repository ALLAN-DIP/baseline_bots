FROM pcpaquette/tensorflow-serving:20190226

WORKDIR /model/src/model_server

RUN apt-get -y update
RUN apt-get -y install git
RUN apt-get -y install vim
RUN apt-get -y install curl
RUN apt-get -y install htop
RUN apt-get -y install lsof

# Copy SL model
RUN mkdir /model/src/model_server/bot_neurips2019-sl_model
COPY bot_neurips2019-sl_model /model/src/model_server/bot_neurips2019-sl_model 
COPY run_model_server.sh /model/src/model_server/run_model_server.sh
RUN chmod 777 /model/src/model_server/run_model_server.sh
RUN chmod -R 777 /model/src/model_server/bot_neurips2019-sl_model

# TODO: Get this to work for RL model as well

# Clone repos
RUN git clone https://github.com/SHADE-AI/diplomacy.git
RUN git clone https://github.com/SHADE-AI/research.git
RUN git clone --single-branch --branch containerizing https://github.com/ALLAN-DIP/baseline_bots.git

# Environment variables
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=cpp
ENV PYTHONIOENCODING=utf-8
ENV LANG=en_CA.UTF-8
ENV PYTHONUNBUFFERED=1
ENV PATH=/data/env3.7/bin:$PATH

# Default batching parameters, can override with docker run -e 
ENV MAX_BATCH_SIZE=128
ENV BATCH_TIMEOUT_MICROS=250000
ENV MAX_ENQUEUED_BATCHES=1024
ENV NUM_BATCH_THREADS=8
ENV PAD_VARIABLE_LENGTH_INPUTS='true'

# Avoid git issues
RUN git config --global --add safe.directory /model/src/model_server/diplomacy
RUN git config --global --add safe.directory /model/src/model_server/research
RUN git config --global --add safe.directory /model/src/model_server/baseline_bots

# Avoid pip issues
RUN pip install --upgrade pip

# Install diplomacy research requirements
WORKDIR /model/src/model_server/research
RUN sed -i 's/gym>/gym=/g'  requirements.txt
RUN pip install -r requirements.txt

# Install baseline_bots requirements
WORKDIR /model/src/model_server/baseline_bots
RUN pip install -r requirements.txt
RUN pip install -e .

# Script executors
COPY run_bot.py /model/src/model_server/baseline_bots/run_bot.py
COPY run.sh /model/src/model_server/baseline_bots/run.sh
RUN chmod 777 /model/src/model_server/baseline_bots/run_bot.py
RUN chmod 777 /model/src/model_server/baseline_bots/run.sh

RUN git clone -b dev --single-branch https://github.com/SHADE-AI/diplomacy-playground.git
RUN cd diplomacy-playground && ls && git status
RUN pip install -r requirements.txt && cd ..

ENTRYPOINT [ "/model/src/model_server/baseline_bots/run.sh" ]

# install dip research and baseline bots
# RUN git clone https://github.com/diplomacy/research.git && \
# git clone https://github.com/ALLAN-DIP/baseline_bots.git && \
# cd baseline_bots && \
# git checkout -b test_CI remotes/origin/test_CI && \
# pip3 install -r requirements.txt && \
# cd ..

# RUN cd / && ls -a && cd research && \ 
# pip3 install -r requirements.txt && \
# pip3 install -r requirements_dev.txt
# RUN cd ../baseline_bots && \
# pip3 install -e . && \
# python3 -m pytest tests/utils_test.py && \
# python3 -m pytest tests/bot_tests/bots_test.py && \
# python3 -m pytest tests/randomize_order_test.py



# FROM ubuntu:18.04

# install updates and use python3.7
# RUN apt-get update -y && \
# apt-get upgrade -y && \
# apt-get install -y python3.7 python3-pip && \
# cd /usr/bin && ls -lrth python* && \
# unlink python3 && ln -s /usr/bin/python3.7 python3
# install necessary packages
# RUN pip3 install --upgrade pip && \
# apt-get install -y git && \
# apt-get install -y wget && \

# install singularity
# RUN export VERSION=v3.2.0  && \
# apt-get update -y  && \
# apt-get install -y build-essential libssl-dev uuid-dev libgpgme11-dev libseccomp-dev pkg-config squashfs-tools  && \
# Installing GO 1.12.5
# export GO_VERSION=1.12.5 OS=linux ARCH=amd64  && \
# wget -nv https://dl.google.com/go/go$GO_VERSION.$OS-$ARCH.tar.gz  && \
# tar -C /usr/local -xzf go$GO_VERSION.$OS-$ARCH.tar.gz  && \
# rm -f go$GO_VERSION.$OS-$ARCH.tar.gz  && \
# export GOPATH=$HOME/.go  && \
# export PATH=/usr/local/go/bin:${PATH}:${GOPATH}/bin  && \
# mkdir -p $GOPATH  && \
# go get github.com/golang/dep/cmd/dep  && \
# Building from source
# mkdir -p $GOPATH/src/github.com/sylabs  && \
# cd $GOPATH/src/github.com/sylabs  && \
# git clone https://github.com/sylabs/singularity.git  && \
# cd singularity  && \
# git checkout $VERSION  && \
# ./mconfig -p /usr/local  && \
# cd ./builddir  && \
# make  && \
# make install
# run tests