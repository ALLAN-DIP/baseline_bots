FROM ubuntu:18.04

# install updates
RUN apt-get update && \
apt-get upgrade -y && \
# install python3
apt-get install -y python3.7 && \
# install pip3
apt-get install -y python3-pip && \
# install git
apt-get install -y git 
# clone dip research repo
# git clone https://github.com/diplomacy/research.git && \
# # install requirements
# pip3 install -r research/requirements.txt && \
# pip3 install -r research/requirements_dev.txt




apt-get install -y python
apt-get install -y python3.7
apt-get install wget

# https://stackoverflow.com/questions/28852841/install-anaconda-on-ubuntu-or-linux-via-command-line
wget https://repo.anaconda.com/archive/Anaconda3-2020.07-Linux-x86_64.sh
bash Anaconda3-2020.07-Linux-x86_64.sh
bash

# should use conda env with python version 3.6
then run dip research installs

apt-get install -y python-pip

# seems pip is needed instead of pip3

# /but pip3 is needed for ujson? can use anaconda instead
apt-get install build-essential python3 python-dev python3-dev

conda install -c anaconda ujson

conda install python=3.6

then run installs


# need to install locale for weird utc8 string stuff
echo "LC_ALL=en_US.UTF-8" >> /etc/environment
echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
echo "LANG=en_US.UTF-8" > /etc/locale.conf
locale-gen en_US.UTF-8 # fails

apt-get install locales

locale-gen en_US.UTF-8


apt-get install vim

# then run redis/singularities installs but without sudo


# install docker, no sudo commands
https://docs.docker.com/engine/install/ubuntu/

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null 


service docker start
