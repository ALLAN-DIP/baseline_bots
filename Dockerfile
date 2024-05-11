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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir src/
COPY LICENSE .
COPY README.md .
COPY pyproject.toml .
COPY setup.cfg .
COPY setup.py .
RUN pip install --no-cache-dir -e .

# Copy baseline_bots code into the Docker image
COPY src/ src/

FROM base as run_tests

COPY tests/ tests/

# Test parameter for async tests
ENV ASYNC_TEST_TIMEOUT=180

CMD ["/bin/bash", "-c", "pytest"]

FROM base AS bot

COPY containers/allan_dip_bot/run_bot.py .

# Script executors
ENTRYPOINT ["python", "run_bot.py"]
