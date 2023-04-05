# This file passes all checks from Hadolint (https://github.com/hadolint/hadolint)
# Use the command `hadolint Dockerfile` to test
# Adding Hadolint to `pre-commit` is non-trivial, so the command must be run manually

FROM pcpaquette/tensorflow-serving:20190226 AS base

WORKDIR /model/src/model_server

# Update Git
# Pinned version is a wildcard because Ubuntu doesn't keep older patch versions available
RUN apt-get -y update \
    && apt-get install --no-install-recommends -y 'git=1:2.17.1-1ubuntu0.*' \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy SL model
RUN wget --progress=dot:giga https://f002.backblazeb2.com/file/ppaquette-public/benchmarks/neurips2019-sl_model.zip \
    && mkdir /model/src/model_server/bot_neurips2019-sl_model \
    && unzip neurips2019-sl_model.zip -d /model/src/model_server/bot_neurips2019-sl_model \
    && rm neurips2019-sl_model.zip \
    && chmod -R 777 /model/src/model_server/bot_neurips2019-sl_model

# Clone and prepare research repo
RUN git config --system --add safe.directory /model/src/model_server/research \
    && git clone https://github.com/SHADE-AI/research.git \
    && git --git-dir research/.git/ checkout 78468505b82f37ec298d234ed406d93445cf8281 \
    && sed -i 's/gym>/gym=/g' research/requirements.txt

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

# Later versions of setuptools do not work properly
RUN pip install --no-cache-dir --upgrade pip==23.0.1 setuptools==66.1.1 wheel==0.38.4

# Install diplomacy research requirements
# hadolint ignore=DL3059
RUN pip install --no-cache-dir -r research/requirements.txt

# Install baseline_bots requirements
# hadolint ignore=DL3059
RUN mkdir -p /model/src/model_server/baseline_bots/src
WORKDIR /model/src/model_server/baseline_bots
COPY LICENSE README.md pyproject.toml requirements.txt setup.cfg setup.py /model/src/model_server/baseline_bots/
RUN pip install --no-cache-dir -e .

# Copy baseline_bots code into the Docker image
COPY src/ /model/src/model_server/baseline_bots/src/

FROM base AS dev

# Copy specialized files
COPY containers/ /model/src/model_server/baseline_bots/containers/
COPY docs/ /model/src/model_server/baseline_bots/docs/
COPY scripts/ /model/src/model_server/baseline_bots/scripts/
COPY tests/ /model/src/model_server/baseline_bots/tests/

# Allow the TF server to be run
RUN chmod 777 /model/src/model_server/baseline_bots/containers/allan_dip_bot/run_model_server.sh
# Add diplomacy research to PYTHONPATH
ENV PYTHONPATH=/model/src/model_server/research:$PYTHONPATH

FROM dev as test_ci

CMD ["/bin/bash", "-c", "/model/src/model_server/baseline_bots/containers/allan_dip_bot/run_model_server.sh & pytest"]

FROM base AS allan_dip_bot

# Copy specialized files
COPY containers/allan_dip_bot/ /model/src/model_server/baseline_bots/containers/allan_dip_bot/
RUN chmod -R 777 /model/src/model_server/baseline_bots/containers/allan_dip_bot/

ENV WORKING_DIR=/model/src/model_server/research/WORKING_DIR

# Script executors
ENTRYPOINT ["/model/src/model_server/baseline_bots/containers/allan_dip_bot/run.sh"]
