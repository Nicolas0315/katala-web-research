.PHONY: help test verify benchmark benchmark-live doctor sources

PYTHON ?= python3

help:
	@printf "%s\n" "Katala Web Research developer targets"
	@printf "%s\n" "  make test           Run unit tests"
	@printf "%s\n" "  make verify         Run the full local verifier"
	@printf "%s\n" "  make benchmark      Refresh deterministic benchmark report"
	@printf "%s\n" "  make benchmark-live Run OpenAlex/meta live benchmark via 1Password .env"
	@printf "%s\n" "  make doctor         Show local provider status"
	@printf "%s\n" "  make sources        Show trusted security sources"

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests

verify:
	scripts/verify.sh

benchmark:
	scripts/benchmark-research-quality.py --iterations 30 --out docs/research-quality-benchmark.md

benchmark-live:
	op run --env-file=.env -- scripts/benchmark-research-quality.py --iterations 10 --live-openalex --live-meta --out docs/research-quality-benchmark.md

doctor:
	PYTHONPATH=src $(PYTHON) -m katala_web_research.cli doctor

sources:
	PYTHONPATH=src $(PYTHON) -m katala_web_research.cli sources list --domain security --json
