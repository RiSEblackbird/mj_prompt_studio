.PHONY: format lint typecheck test build run clean

PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

format:
	$(PYTHON) -m ruff format src scripts tests
	$(PYTHON) -m ruff check --fix src scripts tests

lint:
	$(PYTHON) -m ruff check src scripts tests

typecheck:
	$(PYTHON) -m mypy src

test:
	$(PYTHON) -m pytest

build:
	$(PYTHON) -m compileall -q src

run:
	$(PYTHON) -m mj_prompt_studio.app.main

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov
