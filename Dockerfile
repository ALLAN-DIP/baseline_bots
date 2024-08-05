# This file passes all checks from Hadolint (https://github.com/hadolint/hadolint)
# Use the command `hadolint Dockerfile` to test
# Adding Hadolint to `pre-commit` is non-trivial, so the command must be run manually

FROM python:3.7.17-slim-bookworm AS achilles

WORKDIR /bot

RUN apt-get -y update \
    && apt-get -y upgrade \
    && apt-get --no-install-recommends -y install git=1:2.39.2-1.1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip==24.0

COPY requirements-lock.txt .
RUN pip install --no-cache-dir -r requirements-lock.txt

RUN mkdir src/
COPY LICENSE .
COPY README.md .
COPY pyproject.toml .
COPY requirements.txt .
COPY setup.cfg .
COPY setup.py .
RUN pip install --no-cache-dir -e .

# Copy package code into the Docker image
COPY src/ src/

# Script executors
ENTRYPOINT ["python", "-m", "chiron_utils.scripts.run_bot"]

LABEL org.opencontainers.image.source=https://github.com/ALLAN-DIP/chiron-utils
