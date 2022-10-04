ARG PYTHON_VERSION
FROM python:$PYTHON_VERSION
# how to instructions here: https://containers-at-tacc.readthedocs.io/en/latest/containerize-your-code/build_from_dockerfile.html
FROM ubuntu:20.04

# install updates
RUN apt-get update && \
apt-get upgrade -y && \
apt-get install -y vim && \
# install python3
apt-get install -y python3.6 && \
# install pip
apt-get install -y python3-pip && \
# install git
apt-get install -y git && \
# install wget
apt-get install -y wget && \
# clone dip research repo
git clone https://github.com/diplomacy/research.git && \
git clone https://github.com/ALLAN-DIP/baseline_bots.git && \
pip3 install -r baseline_bots/requirements.txt
RUN pip3 install --ignore-installed tensorflow==1.13.1
RUN cd research && pip3 install -r requirements_dev.txt
# Install miniconda
# ENV CONDA_DIR /opt/conda
# RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
# /bin/bash ~/miniconda.sh -b -p /opt/conda
# # Put conda in path so we can use conda activate
# ENV PATH=$CONDA_DIR/bin:$PATH
# needed for conda activate: https://kevalnagda.github.io/conda-docker-tutorial
# SHELL ["/bin/bash", "--login", "-c"]
# RUN conda create -n diplomacy python=3.6 anaconda && \ 
# /bin/bash -c ". activate diplomacy" && \
# # need to install locale for weird utc8 string stuff
# apt-get install locales  && \
# locale-gen en_US.UTF-8  && \
# pip install tensorflow && \
# pip install -r research/requirements.txt && \
# pip install -r research/requirements_dev.txt

# should use conda env with python version 3.6
# then run dip research installs



# seems pip is needed instead of pip3

# /but pip3 is needed for ujson? can use anaconda instead
# apt-get install build-essential python3 python-dev python3-dev



# then run installs


# # need to install locale for weird utc8 string stuff
# echo "LC_ALL=en_US.UTF-8" >> /etc/environment
# echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
# echo "LANG=en_US.UTF-8" > /etc/locale.conf
# locale-gen en_US.UTF-8 # fails


# then run redis/singularities installs but without sudo


# install docker, no sudo commands
# https://docs.docker.com/engine/install/ubuntu/

# curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
#   $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null 


# service docker start
