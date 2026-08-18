include .env

init:
	poetry install

build:
	poetry build

publish:
	poetry publish

flake8:
	poetry run flake8 gn2pg

black:
	poetry run black gn2pg

isort:
	poetry run isort gn2pg

pylint:
	poetry run pylint gn2pg

trans-update-po:
	xgettext -d base -o gn2pg/locale/gn2pg.pot --from-code=UTF-8 --language=Python gn2pg/*.py
	msgmerge --update gn2pg/locale/fr_FR/LC_MESSAGES/gn2pg.po gn2pg/locale/gn2pg.pot

trans-gen-mo:
	msgfmt -o gn2pg/locale/fr_FR/LC_MESSAGES/gn2pg.mo gn2pg/locale/fr_FR/LC_MESSAGES/gn2pg.po

test-start-db:
	@if docker container inspect dbtestgn2pg >/dev/null 2>&1; then \
		if [ "$$(docker inspect --format '{{.State.Running}}' dbtestgn2pg)" = "true" ]; then \
			echo "Database container dbtestgn2pg is already running"; \
		else \
			docker start dbtestgn2pg; \
		fi; \
	else \
		docker run --name dbtestgn2pg --rm -e POSTGRES_USER=dbuser -e POSTGRES_PASSWORD=dbpass -p 5234:5432 -d postgis/postgis:latest; \
	fi

test: $(if $(filter true,$(TEST_START_DB)),test-start-db) # non-functional

	# @echo ""
	# @echo "Waiting for database \"ready for connections\""
	# @while [ -z "$$(docker logs dbtestgn2pg 2>&1 | grep -o "database system is ready to accept connections")" ]; \
	# do \
	# 	echo "test";sleep 5; \
	# done
	# @echo "Database Ready for connections!"
	# docker logs dbtestgn2pg | grep "database system is ready to accept connections"
	poetry install
	poetry run pytest --user=${GEONATURE_USER} --password=${GEONATURE_PASSWORD} --url=${GEONATURE_URL} --db-user=$(or $(POSTGRESQL_USER),dbuser) --db-password=$(or $(POSTGRESQL_PASS),dbpass) --db-port=$(or $(POSTGRESQL_PORT),5234) --data-export-id=${GEONATURE_DATA_EXPORT_ID} --nb-threads=${GEONATURE_NB_THREADS} tests

build-docs:
	poetry run sphinx-build -b html -d docs/_build/cache -j auto docs docs/_build/html
