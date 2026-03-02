.PHONY: env shell install clean lock lint lintfix types tests quality

env:
	uv venv

install: # Install everything there is
	uv sync --all-extras --all-groups

clean: # Remove packages that are not specified in pyproject.toml
	make install

lint:
	uv run ruff check cipug tests

lintfix:
	uv run ruff check cipug tests --fix

types:
	uv run basedpyright cipug tests

tests:
	uv run pytest tests

quality:
	make lint
	make types
	make tests
