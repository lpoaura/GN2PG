# Tests

## Launch tests
### Prerequisites
To be able to launch tests, the following arguments must be provided:
- user (same as source user name in config file)
- password (same as source password in config file)
- url (same as source url in config file)
- db-user (admin user of the database)
- db-password (password of the db-user)
- db-port (port number of the database)
- export-id (id of the export)
- nb-threads (number of threads to use for parallelisation)

### Before launching tests...
A Postgresql database must be running on the port which will be specified.
One can run a database easily with docker:

`docker run --name postgresgn2pg -e POSTGRES_USER=dbuser -e POSTGRES_PASSWORD=dbpass -p 5434:5432 -d postgis/postgis:14-3.3-alpine`

Explanations:
- `--name`: name of the container
- `-e POSTGRES_USER`: environment variable defining the admin user name
- `-e POSTGRES_PASSWORD`: environment variable defining the password of the POSTGRES_USER
- `-p 5434:5432`: exposes the port 5432 of the container to the local port 5434
  (you can change this if you wish)
- `-d`: detached mode, the container run "in background"
- `postgis/postgis:14-3.3-alpine`: name of the image to run into the container

### Lauching the tests

If the previous parameters of the postgreSQL container are used, the pytest
command should be:

`pytest --user=<my_user> --password=<my_password> --url=<my_url> --db-user=dbuser --db-password=dbpass --db-port=5434 --export-id=1 --nb-threads=1 tests`
