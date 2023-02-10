FROM pcpaquette/tensorflow-serving:20190226 AS base

WORKDIR /model/src/model_server

# install needed packages
RUN apt-get -y update
RUN apt-get -y install git
RUN apt-get -y install vim
RUN apt-get -y install curl
RUN apt-get -y install htop
RUN apt-get -y install lsof

# Copy SL model
RUN wget https://f002.backblazeb2.com/file/ppaquette-public/benchmarks/neurips2019-sl_model.zip
RUN mkdir /model/src/model_server/bot_neurips2019-sl_model
RUN unzip neurips2019-sl_model.zip -d /model/src/model_server/bot_neurips2019-sl_model
RUN chmod -R 777 /model/src/model_server/bot_neurips2019-sl_model

# Clone repos
RUN git clone https://github.com/SHADE-AI/diplomacy.git
RUN git clone https://github.com/SHADE-AI/research.git

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

# Test parameter for async tests
ENV ASYNC_TEST_TIMEOUT=180

# Avoid git issues
RUN git config --global --add safe.directory /model/src/model_server/diplomacy
RUN git config --global --add safe.directory /model/src/model_server/research

# Avoid pip issues
RUN pip install --upgrade pip

# Install diplomacy research requirements
WORKDIR /model/src/model_server/research
RUN sed -i 's/gym>/gym=/g'  requirements.txt
RUN pip install -r requirements.txt

# Install baseline_bots requirements
RUN mkdir -p /model/src/model_server/baseline_bots/src
WORKDIR /model/src/model_server/baseline_bots
COPY README.md pyproject.toml requirements.txt setup.py /model/src/model_server/baseline_bots/
RUN pip install -r requirements.txt
RUN pip install -e .

# copy baseline bots code into the docker image
COPY src/ /model/src/model_server/baseline_bots/src/

FROM base AS dev

# Copy specialized files
COPY containers/ /model/src/model_server/baseline_bots/containers/
COPY docs/ /model/src/model_server/baseline_bots/docs/
COPY scripts/ /model/src/model_server/baseline_bots/scripts/
COPY tests/ /model/src/model_server/baseline_bots/tests/

# allow the tf server to be run
RUN chmod 777 /model/src/model_server/baseline_bots/containers/allan_dip_bot/run_model_server.sh
# add diplomacy research to python path
ENV PYTHONPATH=/model/src/model_server/research:$PYTHONPATH

FROM dev as test_ci

CMD /bin/bash -c '/model/src/model_server/baseline_bots/containers/allan_dip_bot/run_model_server.sh & pytest'

FROM base AS allan_dip_bot

# Copy specialized files
COPY containers/allan_dip_bot/ /model/src/model_server/baseline_bots/containers/allan_dip_bot/
RUN chmod -R 777 /model/src/model_server/baseline_bots/containers/allan_dip_bot/

# Script executors
ENTRYPOINT ["/model/src/model_server/baseline_bots/containers/allan_dip_bot/run.sh"]
