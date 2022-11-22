FROM ubuntu:18.04
RUN mkdir research
RUN mkdir baseline_bots
RUN rm /bin/sh && ln -s /bin/bash /bin/sh
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y install python3.7
RUN touch ~/.bash_profile && echo "alias python='/usr/bin/python3.7'" > ~/.bash_profile && source ~/.bash_profile
RUN apt -y install software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt-get -y install git
RUN apt-get -y install python3-pip
RUN apt-get install wget
RUN apt-get install -y build-essential libssl-dev uuid-dev libgpgme11-dev libseccomp-dev pkg-config squashfs-tools
RUN pip3 install --upgrade setuptools
RUN git clone https://github.com/SHADE-AI/research.git && cd research && pip3 install -r requirements.txt
COPY . /research/ 
RUN cd $HOME
RUN git clone https://github.com/ALLAN-DIP/baseline_bots.git && cd baseline_bots
ADD . baseline_bots/
RUN cd $HOME
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

RUN cd $HOME/baseline_bots
RUN pip3 install git+https://github.com/trigaten/DAIDE

RUN chmod 777 dip_ui_bot_launcher.py
ENV PATH=/baseline_bots/:$PATH
ENV PYTHONPATH=$PYTHONPATH:$ROOT/research/


ENTRYPOINT ["python", "dip_ui_bot_launcher.py","-H","hostname","-p","powers","-B", "bots", "-g", "gameid"]