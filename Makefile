.PHONY: format lint typecheck test build package run run-api run-react run-desktop package-desktop client-install client-lint client-typecheck client-test client-build generate-openapi e2e clean

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

package: client-build
	$(PYTHON) -m build

run:
	PYTHON="$(PYTHON)" $(PYTHON) scripts/run_local_app.py --client-command dev

run-api:
	$(PYTHON) -m mj_prompt_studio.server.main

run-react:
	cd client && npm run dev -- --host 127.0.0.1 --port 5173

run-desktop: run

package-desktop: client-build package

client-install:
	cd client && npm install

client-lint:
	cd client && npm run lint

client-typecheck:
	cd client && npm run typecheck

client-test:
	cd client && npm run test:run

client-build:
	cd client && npm run build

generate-openapi:
	$(PYTHON) scripts/generate_openapi.py

e2e:
	cd client && npm run e2e

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov client/dist client/playwright-report client/test-results
