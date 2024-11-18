set dotenv-load := true

# By default, run checks and tests, then format and lint
default:
  @just format
  @just check
  @just test
  @just lint

#
# Installing, updating and upgrading dependencies
#

# Sync project
sync:
  uv sync --extra dev
  uv pip install -e .

#
# Development tooling - linting, formatting, etc
#

# Run a command or script
run *argv:
  uv run {{ argv }}

# Format with black and isort
format:
  uv run black ./flag ./tests ./examples
  uv run isort --settings-file . ./flag ./tests ./example

# Lint with flake8
lint:
  uv run flake8 ./flag ./tests ./examples
  uv run validate-pyproject ./pyproject.toml
  shellcheck ./scripts/*.sh

# Check type annotations with pyright
check:
  uv run npx pyright@latest

# Run tests with pytest
test:
  uv run pytest ./tests
  @just _clean-test

_clean-test:
  rm -f pytest_runner-*.egg
  rm -rf tests/__pycache__

#
# Shell and console
#

shell:
  uv run bash

console:
  uv run jupyter console

#
# Documentation
#

# Live generate docs and host on a development webserver
docs:
  uv run mkdocs serve

# Build the documentation
build-docs:
  uv run mkdocs build

#
# Package publishing
#

# Build the package
build:
  uv build

_clean-build:
  rm -rf dist

# Tag the release in git
tag:
  git tag -a "$(uv run python3 -c 'import toml; print(toml.load(open("pyproject.toml", "r"))["project"]["version"])')" -m "Release $(uv run python3 -c 'import toml; print(toml.load(open("pyproject.toml", "r"))["project"]["version"])')"

# Publish the release
publish: build
  ./scripts/publish.sh

# Clean up loose files
clean: _clean-test
  rm -rf go-flag.egg-info
  rm -f flag/*.pyc
  rm -rf flag/__pycache__
