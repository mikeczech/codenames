.PHONY: install run

install:
	poetry install

run-backend:
	FLASK_APP=codenames \
  FLASK_ENV=development \
  poetry run flask run

run-frontend:
	(cd frontend && npm start)

init-db:
	FLASK_APP=codenames \
  FLASK_ENV=development \
  poetry run flask init-db
