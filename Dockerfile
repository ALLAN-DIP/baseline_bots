# This file passes all checks from Hadolint (https://github.com/hadolint/hadolint)
# Use the command `hadolint Dockerfile` to test
# Adding Hadolint to `pre-commit` is non-trivial, so the command must be run manually

FROM python:3.7.17-slim-bookworm AS base

WORKDIR /bot

# Update Git
# Pinned version is a wildcard because Ubuntu doesn't keep older patch versions available
RUN apt-get -y update \
    && apt-get --no-install-recommends -y install git=1:2.39.2-1.1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Later versions of pip and setuptools do not work properly
RUN pip install --no-cache-dir --upgrade pip==24.0

# Install baseline_bots requirements
# hadolint ignore=DL3059
RUN mkdir -p /model/src/model_server/baseline_bots/src
WORKDIR /model/src/model_server/baseline_bots

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY LICENSE .
COPY README.md .
COPY pyproject.toml .
COPY setup.cfg .
COPY setup.py .
RUN pip install --no-cache-dir -e .

# Copy baseline_bots code into the Docker image
COPY src/ src/

FROM base AS dev

# Copy specialized files
COPY containers/ /model/src/model_server/baseline_bots/containers/
COPY scripts/ /model/src/model_server/baseline_bots/scripts/
COPY tests/ /model/src/model_server/baseline_bots/tests/

FROM dev as test_ci

# Test parameter for async tests
ENV ASYNC_TEST_TIMEOUT=180

CMD ["/bin/bash", "-c", "pytest"]

FROM base AS allan_dip_bot

# Script executors
ENTRYPOINT ["/bot/run.sh"]
