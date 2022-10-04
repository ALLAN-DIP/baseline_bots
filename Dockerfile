FROM ubuntu:20.04

# install updates
RUN apt list --installed && apt-get update && \
apt-get upgrade -y && \
apt-get install -y python==3.6 python3-dev python3-pip
RUN python --version
# apt-get install -y python3.6 python-dev python3-dev python3-pip && \
# apt-get install -y git && \
# apt-get install -y wget && \
# git clone https://github.com/diplomacy/research.git && \
# git clone https://github.com/ALLAN-DIP/baseline_bots.git && \
# pip3 install -r baseline_bots/requirements.txt
# SHELL ["/bin/bash", "--login", "-c"]
# RUN pip3 install -r research/requirements.txt && \
# pip3 install -r research/requirements_dev.txt