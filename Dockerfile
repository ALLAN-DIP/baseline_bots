FROM ubuntu:18.04

# install updates and use python3.7
RUN apt-get update -y && \
apt-get upgrade -y && \
apt-get install -y python3.7 python3-pip && \
cd /usr/bin && ls -lrth python* && \
unlink python3 && ln -s /usr/bin/python3.7 python3
# install necessary packages
RUN pip3 install --upgrade pip && \
apt-get install -y git && \
apt-get install -y wget && \
git clone https://github.com/diplomacy/research.git && \
git clone https://github.com/ALLAN-DIP/baseline_bots.git && \
cd baseline_bots && \
git checkout -b test_CI remotes/origin/test_CI && \
pip3 install -r requirements.txt && \
cd ..
# install singularity
RUN export VERSION=v3.2.0  && \
sudo apt-get update -y  && \
sudo apt-get install -y build-essential libssl-dev uuid-dev libgpgme11-dev libseccomp-dev pkg-config squashfs-tools  && \
# Installing GO 1.12.5
export GO_VERSION=1.12.5 OS=linux ARCH=amd64  && \
wget -nv https://dl.google.com/go/go$GO_VERSION.$OS-$ARCH.tar.gz  && \
sudo tar -C /usr/local -xzf go$GO_VERSION.$OS-$ARCH.tar.gz  && \
rm -f go$GO_VERSION.$OS-$ARCH.tar.gz  && \
export GOPATH=$HOME/.go  && \
export PATH=/usr/local/go/bin:${PATH}:${GOPATH}/bin  && \
mkdir -p $GOPATH  && \
go get github.com/golang/dep/cmd/dep  && \
# Building from source
mkdir -p $GOPATH/src/github.com/sylabs  && \
cd $GOPATH/src/github.com/sylabs  && \
git clone https://github.com/sylabs/singularity.git  && \
cd singularity  && \
git checkout $VERSION  && \
./mconfig -p /usr/local  && \
cd ./builddir  && \
make  && \
sudo make install && pwd
# run tests
RUN cd research && \ 
pip3 install -r requirements.txt && \
pip3 install -r requirements_dev.txt
RUN cd ../baseline_bots && \
pip3 install -e . && \
python3 -m pytest tests/utils_test.py && \
python3 -m pytest tests/bot_tests/bots_test.py && \
python3 -m pytest tests/randomize_order_test.py
