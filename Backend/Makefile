.PHONY: install run lint openapi

install:
	python -m pip install -r requirements.txt

run:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

lint:
	bash scripts/lint.sh

openapi:
	python -m src.api.generate_openapi
