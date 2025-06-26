# Haravajärjestelmä

:fallen_leaf: API for volunteer work events :fallen_leaf:

## Development with Docker

1. Copy `compose.env.example` to `compose.env` and modify it if needed.

2. Run `docker compose up`

3. Import geo data
    * `docker exec -it haravajarjestelma-backend python manage.py geo_import --municipalities finland`
    * `docker exec -it haravajarjestelma-backend python manage.py geo_import --addresses helsinki`
    * `docker exec -it haravajarjestelma-backend python manage.py import_helsinki_contract_zones`

The project is now running at [localhost:8085](http://localhost:8085)

## Development without Docker

### Install pip-tools

* Run `pip install pip-tools`

### Creating Python requirements files

* Run `pip-compile requirements.in`

### Updating Python requirements files

* Run `pip-compile --upgrade requirements.in`

### Installing Python requirements

* Run `pip-sync requirements.txt`

### Database

To setup a database compatible with default database settings:

Create user and database

    sudo -u postgres createuser -P -R -S haravajarjestelma  # use password `haravajarjestelma`
    sudo -u postgres createdb -O haravajarjestelma haravajarjestelma

Create extensions in the database

    sudo -u postgres psql haravajarjestelma -c "CREATE EXTENSION postgis;"

Allow user to create test database

    sudo -u postgres psql -c "ALTER USER haravajarjestelma CREATEDB;"

Run migrations if needed:

    python manage.py migrate

Create superuser if needed:

    python manage.py createsuperuser

Import geo data

    python manage.py geo_import --municipalities finland
    python manage.py geo_import --addresses helsinki
    python manage.py import_helsinki_contract_zones

### Daily running

* Set the `DEBUG` environment variable to `1`.
* Run `python manage.py migrate`
* Run `python manage.py runserver 0:8085`

The project is now running at [localhost:8085](http://localhost:8085)

### Periodic tasks

In order to get reminder notifications of upcoming events sent to contractors, `./manage.py send_event_reminder_notifications` needs to be run periodically, preferably daily.

### Settings

The following settings can be used to configure the application either using environment variables or `local_settings.py`:

* `EXCLUDED_CONTRACT_ZONES`: List of names of contract zones that should not be imported. Default `[]`.

  Example env: `EXCLUDED_CONTRACT_ZONES=Itä-Helsingin kartanopihat,Suomenlinna`

* `EVENT_MINIMUM_DAYS_BEFORE_START`: Minimum amount of days an event needs to be created in advance before it's start. Default `7`.

* `EVENT_MAXIMUM_COUNT_PER_CONTRACT_ZONE`: Maximum amount of events there can be on one day per contract zone. Default: `3`.

* `EVENT_REMINDER_DAYS_IN_ADVANCE`: Number of days event reminders to contractors are sent in advance. Default `2`.

* `HELSINKI_WFS_BASE_URL`: Base URL of Helsinki WFS API that is used as the source for contract zones. Default `https://kartta.hel.fi/ws/geoserver/avoindata/wfs`.

## Code format

This project uses
[`black`](https://github.com/ambv/black),
[`flake8`](https://gitlab.com/pycqa/flake8) and
[`isort`](https://github.com/pycqa/isort)
for code formatting and quality checking. Project follows the basic
black config, without any modifications.

Basic `black` commands:

* To let `black` do its magic: `black .`
* To see which files `black` would change: `black --check .`

[`pre-commit`](https://pre-commit.com/) can be used to install and
run all the formatting tools as git hooks automatically before a
commit.

## Commit message format

New commit messages must adhere to the [Conventional Commits](https://www.conventionalcommits.org/)
specification, and line length is limited to 72 characters.

When [`pre-commit`](https://pre-commit.com/) is in use, [`commitlint`](https://github.com/conventional-changelog/commitlint)
checks new commit messages for the correct format.


## API documentation

OpenAPI 3 definition of the API can be found [here](openapi.yaml).

## Git blame ignore refs

Project includes a `.git-blame-ignore-revs` file for ignoring certain commits from `git blame`.
This can be useful for ignoring e.g. formatting commits, so that it is more clear from `git blame`
where the actual code change came from. Configure your git to use it for this project with the
following command:

```shell
git config blame.ignoreRevsFile .git-blame-ignore-revs
```
