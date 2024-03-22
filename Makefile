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
	docker build --target test_ci --tag ci_image .
	docker run --rm ci_image

.PHONY: check
check: precommit test

.PHONY: build
build:
	docker build \
		--target allan_dip_bot \
		--tag allan_dip_bot \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		--cache-from allanumd/allan_bots:base-latest \
		.
