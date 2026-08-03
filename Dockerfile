# ==============================
FROM helsinki.azurecr.io/ubi9/python-312-gdal AS appbase
# ==============================

# Branch or tag used to pull python-uwsgi-common.
ARG UWSGI_COMMON_REF=main

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# uv configuration
ENV UV_PROJECT_ENVIRONMENT=/opt/app-root \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PYTHON_DOWNLOADS=never
ENV PATH="${UV_PROJECT_ENVIRONMENT}/bin:${PATH}"

COPY --from=ghcr.io/astral-sh/uv:0.12.1@sha256:cf4eedcaa81655197f625739489effcbe71b61ceb1506f332c3facae5deceded /uv /uvx /usr/local/bin/

WORKDIR /app

USER root

COPY pyproject.toml uv.lock ./

RUN dnf update -y && \
    dnf install -y nmap-ncat && \
    dnf clean all && \
    uv sync --locked --no-install-project --no-dev --group prod

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

RUN uv sync --locked --no-install-project --all-groups

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
