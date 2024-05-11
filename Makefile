.PHONY: default
default:
	@echo "an explicit target is required"

SHELL=/usr/bin/env bash

export PYTHONPATH := $(shell realpath .)

.PHONY: precommit
precommit:
	pre-commit run --all-files

.PHONY: test
test:
	export ASYNC_TEST_TIMEOUT=180 && \
	pytest

.PHONY: check
check: precommit test

.PHONY: build
build:
	docker build \
		--target achilles \
		--tag achilles \
		.
