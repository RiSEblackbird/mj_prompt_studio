.PHONY: format lint typecheck test build package run clean

PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

# Apple Silicon では Rosetta/x86_64 の Python が arm64 向け wheel を読めず pydantic 等が落ちる。
ifeq ($(shell uname -s 2>/dev/null),Darwin)
  ifeq ($(shell sysctl -n hw.optional.arm64 2>/dev/null),1)
    PY_MACHINE := $(shell $(PYTHON) -c 'import platform; print(platform.machine())' 2>/dev/null || echo unknown)
    ifeq ($(PY_MACHINE),x86_64)
      PYTHON := arch -arm64 $(PYTHON)
    endif
  endif
endif

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

package:
	$(PYTHON) -m build

run:
	$(PYTHON) -m mj_prompt_studio.app.main

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov
