.PHONY: install run

install:
	poetry install
	(cd frontend && npm install)

format:
	poetry run black codenames/
	poetry run black tests/

run-tests:
	poetry run pytest tests/codenames

run-backend:
	FLASK_APP=codenames \
  FLASK_ENV=development \
  poetry run flask run

run-frontend:
	(cd frontend && npm start)

run-jupyter:
	poetry run jupyter lab

init-db:
	mkdir instance
	FLASK_APP=codenames \
  FLASK_ENV=development \
  poetry run flask init-db
