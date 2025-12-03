# ==============================
FROM helsinki.azurecr.io/ubi9/python-312-gdal AS appbase
# ==============================

# Branch or tag used to pull python-uwsgi-common.
ARG UWSGI_COMMON_REF=main

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

USER root

COPY requirements.txt .

RUN dnf update -y && \
    dnf install -y nmap-ncat && \
    dnf clean all && \
    pip install -U pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Build and copy specific python-uwsgi-common files.
ADD https://github.com/City-of-Helsinki/python-uwsgi-common/archive/${UWSGI_COMMON_REF}.tar.gz /usr/src/
RUN mkdir -p /usr/src/python-uwsgi-common && \
    tar --strip-components=1 -xzf /usr/src/${UWSGI_COMMON_REF}.tar.gz -C /usr/src/python-uwsgi-common && \
    cp /usr/src/python-uwsgi-common/uwsgi-base.ini /app/ && \
    uwsgi --build-plugin /usr/src/python-uwsgi-common && \
    rm -rf /usr/src/${UWSGI_COMMON_REF}.tar.gz && \
    rm -rf /usr/src/python-uwsgi-common

# Install uWSGI Sentry plugin
RUN mkdir -p /usr/local/lib/uwsgi/plugins && \
    uwsgi --build-plugin https://github.com/City-of-Helsinki/uwsgi-sentry && \
    mv sentry_plugin.so /usr/local/lib/uwsgi/plugins/

ENTRYPOINT ["/app/docker-entrypoint.sh"]

# ==============================
FROM appbase AS development
# ==============================

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

ENV DEV_SERVER=1

COPY . .

# django-munigeo municipality importer requires this
RUN mkdir -p /app/data && chgrp -R 0 /app/data && chmod g+w -R /app/data

USER default
EXPOSE 8000/tcp

# ==============================
FROM appbase AS production
# ==============================

COPY . .

# django-munigeo municipality importer requires this
RUN mkdir -p /app/data && chgrp -R 0 /app/data && chmod g+w -R /app/data

RUN SECRET_KEY="only-used-for-collectstatic" python manage.py collectstatic && python manage.py compilemessages

USER default
EXPOSE 8000/tcp
