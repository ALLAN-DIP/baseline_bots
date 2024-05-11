# This file passes all checks from Hadolint (https://github.com/hadolint/hadolint)
# Use the command `hadolint Dockerfile` to test
# Adding Hadolint to `pre-commit` is non-trivial, so the command must be run manually

FROM python:3.7.17-slim-bookworm AS base

WORKDIR /bot

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

FROM base AS bot

COPY scripts/run_bot.py .

# Script executors
ENTRYPOINT ["python", "run_bot.py"]
