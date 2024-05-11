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
	docker build --target run_tests --tag achilles:testing .
	docker run --rm achilles:testing

.PHONY: check
check: precommit test

.PHONY: build
build:
	docker build \
		--target bot \
		--tag achilles \
		.
