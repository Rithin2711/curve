.PHONY: install run lint openapi

install:
\tpython -m pip install -r requirements.txt

run:
\tuvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

lint:
\tbash scripts/lint.sh

openapi:
\tpython -m src.api.generate_openapi
