.PHONY: install format check test evaluate run docker-build docker-run

install:
	python -m pip install -e '.[dev]'

format:
	python -m ruff format .
	python -m ruff check . --fix

check:
	python -m ruff format --check .
	python -m ruff check .
	python -m mypy src tests

test:
	python -m pytest

evaluate:
	labos-evaluate

run:
	python -m streamlit run app.py

docker-build:
	docker build -t labos-operations-copilot .

docker-run:
	docker run --rm \
		-p 8501:8501 \
		--env-file .env \
		labos-operations-copilot