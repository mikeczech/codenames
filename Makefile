.PHONY: install run

install:
	poetry install

run:
	FLASK_APP=codenames \
  FLASK_ENV=development \
  poetry run flask run

init-db:
	FLASK_APP=codenames \
  FLASK_ENV=development \
  poetry run flask init-db
