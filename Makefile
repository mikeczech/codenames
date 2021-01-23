.PHONY: install run

install:
	poetry install

format:
	poetry run black codenames/

run-backend:
	FLASK_APP=codenames \
  FLASK_ENV=development \
  poetry run flask run

run-frontend:
	(cd frontend && npm start)

run-jupyter:
	poetry run jupyter lab

init-db:
	FLASK_APP=codenames \
  FLASK_ENV=development \
  poetry run flask init-db
