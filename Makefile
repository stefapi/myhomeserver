PYTHON ?= python3
LIBRARY=myeasyserver
PYTHON_VERSION = $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_version; print(get_python_version())")
SITELIB=$(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
PACKER ?= packer
PACKER_BUILD_OPTS ?= -var 'official=$(OFFICIAL)' -var 'mp_repo_url=$(MP_REPO_URL)'
DOCKER ?= docker
DOCKER_COMPOSE ?= docker-compose
NODE ?= node
POETRY ?= poetry
NPM_BIN ?= npm
YARN_BIN ?= yarn
DEPS_SCRIPT ?= packaging/bundle/deps.py
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)

VERSION=$(shell git describe --long --first-parent)
VERSION3=$(shell git describe --long --first-parent | sed 's/\-g.*//')
VERSION3DOT=$(shell git describe --long --first-parent | sed 's/\-g.*//' | sed 's/\-/\./')
RELEASE_VERSION=$(shell git describe --long --first-parent | sed 's@\([0-9.]\{1,\}\).*@\1@')

# NOTE: This defaults the container image version to the branch that's active
COMPOSE_TAG ?= $(GIT_BRANCH)
COMPOSE_HOST ?= $(shell hostname)

VENV_BASE ?= ./venv

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

define RUN_PYSCRIPT
from $(LIBRARY) import create_app
app = create_app()
app.run()
endef
export RUN_PYSCRIPT

define DEBUG_PYSCRIPT
from $(LIBRARY) import create_app
app = create_app()
app.run()
endef
export DEBUG_PYSCRIPT

BROWSER := $(PYTHON) -c "$$BROWSER_PYSCRIPT"

help: ##    Details Makefile help
	@$(PYTHON) -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

.ONESHELL:

.PHONY: docs

outdated: ## 🚧 Check for outdated dependencies
	$(POETRY) show --outdated

setup: ## 🏗 Setup installation in order to start working
	$(POETRY) install --with main,dev
	@echo "🏗  Development Setup Complete "
	@echo "❗️ Tips"
	@echo "    1. run 'make backend' to start the API server"

# -----------------------------------------------------------------------------
# Clean makefile

clean-data: ## ⚠️  Removes All Developer Data for a fresh server start
	rm -r ./dev/data/users/
	rm -f ./dev/data/*.db
	rm -f ./dev/data/*.log
	rm -f ./dev/data/.secret

clean_build: ## 🧹 Clean python build files
	rm -rf build dist .eggs
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

#clean_docs: ## 🧹 Clean documentation build
	rm -rf docs/_build

clean_tests: ## 🧹 Remove test and coverage artifacts
	rm -f .coverage
	rm -rf .tox
	rm -rf htmlcov
	rm -rf .pytest_cache

clean_pyc: ## 🧹 Remove python files artifacts
	find ./$(LIBRARY) -type f -name '*.pyc' -delete
	find ./$(LIBRARY) -type f -name '*.log' -delete
	find ./$(LIBRARY) -type f -name '*~' -delete
	find ./$(LIBRARY) -name '__pycache__' -exec rm -fr {} +

clean_back_client: ## 🧹 Remove client UI build artifacts
	rm -rf $(LIBRARY)/dist

clean: clean-data backend-clean ## 🧹 Remove all build, test, coverage and Python artifacts

# -----------------------------------------------------------------------------
# Backend makefile

backend-clean: clean_pyc clean_tests clean_back_client ## 🧹 Remove all build, test, coverage and Python artifacts
	rm -fr .mypy_cache

backend-typecheck:
	$(POETRY) run mypy $(LIBRARY)

backend-build: ## 🏗  Build backend
	$(POETRY) build

backend-test: ## 🧪 Run tests quickly with the default Python
	$(POETRY) run pytest

backend-format: ## 🧺 Format the codebase
	$(POETRY) run black .

backend-lint: ## 🧹 Lint the codebase (Ruff)
	$(POETRY) run ruff $(LIBRARY)

backend-all: backend-format backend-lint backend-typecheck backend-test ## 🧪 Runs all the backend checks and tests

backend-coverage: ## ☂️  Check code coverage quickly with the default Python
	$(POETRY) run pytest
	$(POETRY) run coverage report -m
	$(POETRY) run coveragepy-lcov
	$(POETRY) run coverage html
	$(BROWSER) htmlcov/index.html

.PHONY: backend
backend: ## 🎬 Start Backend Development Server
	$(POETRY) run $(PYTHON) $(LIBRARY)/db/init_db.py && \
	$(POETRY) run $(PYTHON) $(LIBRARY)/app.py

vagrant-up: ## 🎬 Start Vagrant Server
	vagrant up homeserverdebug

purge: clean ## 🧹 Remove everything not needed to rebuild a fresh environment
	rm -rf ./dev/data
	$(POETRY) env remove
	vagrant destroy

prepare: ## 🏗 Prepare everything for deployment
	poetry export --output requirements.txt
	$(POETRY) run dev/scripts/project_identity.py

format: backend-format ## 🧺 Format the codebase

lint: backend-lint ## 🧹 Lint the codebase

tests: backend-test ## 🧪 Tests both server and client

serve: ## 🎬 serve client and server separately
	$(POETRY) run $(PYTHON) -c "$$DEBUG_PYSCRIPT"

run: ## 🎬 Run server as in production
	$(POETRY) run $(PYTHON) -c "$$RUN_PYSCRIPT"

dist: clean prepare  backend-build ## 🐳 Create dist files

docs: ## 📄 Format document and start server
	$(POETRY) run $(PYTHON) dev/scripts/api_docs_gen.py && \
	cd docs && $(POETRY) run $(PYTHON) -m mkdocs serve

release: clean dist ## 🐳 Build and publish on pypi
	$(POETRY) publish

release-install: ## 🐳 install production version
	pip install $(LIBRARY) --break-system-packages

stage: clean dist ## 🐳 Build and publish on testpypi
	$(POETRY) config repositories.testpypi https://test.pypi.org/legacy/
	$(POETRY) publish -r testpypi

stage-install: ## 🐳 install testing version published on testpypi
	pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ $(LIBRARY) --break-system-packages

install: ## 🐳 install development version
	pip install -e . --break-system-packages

all: clean setup format lint tests run
