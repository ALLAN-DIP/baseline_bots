# This file passes all checks from Hadolint (https://github.com/hadolint/hadolint)
# Use the command `hadolint Dockerfile` to test
# Adding Hadolint to `pre-commit` is non-trivial, so the command must be run manually

FROM allanumd/allan_bots:model_zip as model_zip

FROM pcpaquette/tensorflow-serving:20190226 AS base

WORKDIR /model/src/model_server

# Update Git
# Pinned version is a wildcard because Ubuntu doesn't keep older patch versions available
RUN apt-get -y update \
    && apt-get install --no-install-recommends -y 'git=1:2.17.1-1ubuntu0.*' \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Test parameter for async tests
ENV ASYNC_TEST_TIMEOUT=180

# Later versions of pip and setuptools do not work properly
RUN pip install --no-cache-dir --upgrade pip==23.0.1 setuptools==66.1.1 wheel==0.40.0

# Install baseline_bots requirements
# hadolint ignore=DL3059
RUN mkdir -p /model/src/model_server/baseline_bots/src
WORKDIR /model/src/model_server/baseline_bots
COPY LICENSE README.md pyproject.toml requirements.txt setup.cfg setup.py /model/src/model_server/baseline_bots/
RUN pip install --no-cache-dir -e .

# Copy baseline_bots code into the Docker image
COPY src/ /model/src/model_server/baseline_bots/src/

# Generate batch file for running server
COPY containers/allan_dip_bot/ /model/src/model_server/baseline_bots/containers/allan_dip_bot/
RUN chmod -R 777 /model/src/model_server/baseline_bots/containers/allan_dip_bot/

FROM base AS dev

# Copy specialized files
COPY containers/ /model/src/model_server/baseline_bots/containers/
COPY scripts/ /model/src/model_server/baseline_bots/scripts/
COPY tests/ /model/src/model_server/baseline_bots/tests/

FROM dev as test_ci

CMD ["/bin/bash", "-c", "pytest"]

FROM base AS allan_dip_bot

# Script executors
ENTRYPOINT ["/model/src/model_server/baseline_bots/containers/allan_dip_bot/run.sh"]
