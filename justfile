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
  uv sync --all-extras

#
# Development tooling - linting, formatting, etc
#

# Format with black and isort
format:
  uv run black ./flag ./tests
  uv run isort --settings-file . ./flag ./tests

# Lint with flake8
lint:
  uv run flake8 ./flag ./tests
  uv run validate-pyproject ./pyproject.toml

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
  uv run build

_clean-build:
  rm -rf dist

# Tag the release in git
tag:
  uv run git tag -a "$(python3 -c 'import toml; print(toml.load(open("pyproject.toml", "r"))["project"]["version"])')" -m "Release $(python3 -c 'import toml; print(toml.load(open("pyproject.toml", "r"))["project"]["version"])')"

# Upload built packages
upload:
  # TODO: Does uv do this?
  uv run twine upload dist/*

# Build the package and publish it to PyPI
publish: build upload

# Clean up loose files
clean: _clean-test
  rm -rf go-flag.egg-info
  rm -f flag/*.pyc
  rm -rf flag/__pycache__
