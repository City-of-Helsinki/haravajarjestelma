# Haravajärjestelmä

:fallen_leaf: API for volunteer work events :fallen_leaf:

## Development with Docker

1. Copy `docker-compose.env.yaml.example` to `docker-compose.env.yaml` and modify it if needed.

2. Run `docker-compose up`

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

## Code format

This project uses [`black`](https://github.com/ambv/black) for Python code formatting.
We follow the basic config, without any modifications. Basic `black` commands:

* To let `black` do its magic: `black .`
* To see which files `black` would change: `black --check .`
