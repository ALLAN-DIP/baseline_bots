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
COPY containers/test_env/run_model_server.sh /model/src/model_server/run_model_server.sh
RUN chmod 777 /model/src/model_server/run_model_server.sh
RUN chmod -R 777 /model/src/model_server/bot_neurips2019-sl_model

# TODO: Get this to work for RL model as well

# Clone repos
RUN git clone https://github.com/SHADE-AI/diplomacy.git
RUN git clone https://github.com/SHADE-AI/research.git
RUN mkdir /model/src/model_server/baseline_bots

# Run pytests


COPY . /model/src/model_server/baseline_bots

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
RUN pip install -r requirements_dev.txt

# Install baseline_bots requirements
WORKDIR /model/src/model_server/baseline_bots
RUN pip install -r requirements.txt
RUN pip install -e .

# run pytest
RUN pytest tests/utils_test.py
# RUN pytest tests/randomize_order_test.py
RUN pytest tests/bot_tests

# Script executors
RUN chmod 777 /model/src/model_server/baseline_bots/containers/test_env/run_bot.py
RUN chmod 777 /model/src/model_server/baseline_bots/containers/test_env/run.sh

# install diplomacy playground
WORKDIR /
RUN git clone -b dev --single-branch https://github.com/SHADE-AI/diplomacy-playground.git
RUN git config --global --add safe.directory /model/src/model_server/diplomacy-playground
WORKDIR /diplomacy-playground
RUN pip install hashids==1.3.1
RUN pip install -r requirements.txt

WORKDIR /
ENTRYPOINT [ "/model/src/model_server/baseline_bots/containers/test_env/run.sh" ]
