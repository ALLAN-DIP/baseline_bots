FROM ubuntu:18.04
RUN mkdir /baseline_bots
WORKDIR /baseline_bots

RUN apt-get update
RUN apt-get -y upgrade
RUN apt -y install software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt -y install python3.7
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.7 1
RUN apt-get -y install git
RUN apt-get -y install vim
RUN apt-get -y install python3-pip
RUN python -m pip install --upgrade pip
RUN apt-get -y install python3-pip
RUN apt-get install wget
RUN apt-get install -y build-essential libssl-dev uuid-dev libgpgme11-dev libseccomp-dev pkg-config squashfs-tools

RUN git clone https://github.com/SHADE-AI/research.git && cd research && pip3 install -r requirements.txt

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=cpp
ENV PYTHONIOENCODING=utf-8
ENV LANG=en_CA.UTF-8
ENV PYTHONUNBUFFERED=1
ENV PATH=/data/env3.7/bin:$PATH

ENV VERSION=v3.2.0
ENV GO_VERSION=1.12.5 OS=linux ARCH=amd64
ENV GOPATH=$HOME/.go
ENV PATH=/usr/local/go/bin:${PATH}:${GOPATH}/bin
RUN wget -nv https://dl.google.com/go/go$GO_VERSION.$OS-$ARCH.tar.gz && tar -C /usr/local -xzf go$GO_VERSION.$OS-$ARCH.tar.gz && rm -f go$GO_VERSION.$OS-$ARCH.tar.gz && mkdir -p $GOPATH && go get github.com/golang/dep/cmd/dep && mkdir -p $GOPATH/src/github.com/sylabs && cd $GOPATH/src/github.com/sylabs && git clone https://github.com/sylabs/singularity.git && cd singularity && git checkout v3.2.0 &&./mconfig -p /usr/local &&cd ./builddir && make && make install

RUN cd $ROOT/baseline_bots
RUN pip3 install git+https://github.com/trigaten/DAIDE

COPY dip_ui_bot_launcher.py /baseline_bots/dip_ui_bot_launcher.py
COPY utils.py /baseline_bots/utils.py
COPY bots/baseline_bot.py /baseline_bots/bots/baseline_bot.py 
COPY bots/dipnet/loyal_support_proposal.py /baseline_bots/bots/dipnet/loyal_support_proposal.py 
COPY bots/dipnet/no_press_bot.py /baseline_bots/bots/dipnet/no_press_bot.py 
COPY bots/dipnet/dipnet_bot.py /baseline_bots/bots/dipnet/dipnet_bot.py
RUN chmod 777 /baseline_bots/dip_ui_bot_launcher.py
ENV PATH=/baseline_bots:$PATH
ENV PYTHONPATH=$PYTHONPATH:$ROOT/baseline_bots/research/

ENTRYPOINT ["python3", "baseline_bots/dip_ui_bot_launcher.py","-H","hostname","-p","powers","-B", "bots", "-g", "gameid"]