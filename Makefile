.PHONY: sync run test lint format type check hooks build-sprites

sync:
	uv sync

run:
	uv run climon

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

type:
	uv run mypy

check: lint type test
	uv run ruff format --check .

hooks:
	uv run pre-commit install

build-sprites:
	uv run python tools/build_sprites.py
