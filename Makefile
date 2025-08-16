.PHONY: format lint typecheck security check all

format:
	black .
	ruff check . --fix

lint:
	ruff check .

typecheck:
	mypy .

security:
	bandit -r .

check: lint typecheck
all: format lint typecheck security