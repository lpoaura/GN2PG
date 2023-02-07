flake8:
	poetry run flake8 gn2pg

black:
	poetry run black gn2pg

pylint:
	poetry run pylint gn2pg

trans-update-po:
	pygettext3 -d base -o gn2pg/locale/gn2pg.pot gn2pg
	msgmerge --update gn2pg/locale/fr_FR/LC_MESSAGES/gn2pg.po gn2pg/locale/gn2pg.pot

trans-gen-mo:
	msgfmt -o gn2pg/locale/fr_FR/LC_MESSAGES/gn2pg.mo gn2pg/locale/fr_FR/LC_MESSAGES/gn2pg.po

tests:
	docker run --name dbtestgn2pg --rm -e POSTGRES_USER=dbuser -e POSTGRES_PASSWORD=dbpass -p 5234:5432 -d postgis/postgis:latest
	pytest --user=admin --password=admin --url=https://demo.geonature.fr/geonature --db-user=dbuser --db-password=dbpass --db-port=5234 --export-id=1 --nb-threads=1 tests
