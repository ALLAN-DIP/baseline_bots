FROM ubuntu:18.04

# install updates
RUN apt-get update -y && \
apt-get upgrade -y && \
apt-get install -y python3.7 python3-pip && \
cd /usr/bin && ls -lrth python* && \
unlink python3 && ln -s /usr/bin/python3.7 python3 && \
python3 --version
RUN pip3 install --upgrade pip && \
apt-get install -y git && \
apt-get install -y wget && \
git clone https://github.com/diplomacy/research.git && \
git clone https://github.com/ALLAN-DIP/baseline_bots.git && \
cd baseline_bots && \
git checkout -b test_CI remotes/origin/test_CI && \
pip3 install -r requirements.txt && \
cd ..
RUN cd research && \ 
pip3 install -r requirements.txt && \
pip3 install -r requirements_dev.txt
RUN cd ../baseline_bots && \
pip3 install -e . && \
python3 -m pytest tests/utils_test.py && \
python3 -m pytest tests/bot_tests/bots_test.py && \
python3 -m pytest tests/randomize_order_test.py
