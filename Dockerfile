ARG PYTHON_VERSION=3.9
ARG IMAGE_VARIANT=slim
ARG BUILDER_REGISTRY=docker.io

# ==============================
FROM ${BUILDER_REGISTRY}/helsinkitest/python:${PYTHON_VERSION}-${IMAGE_VARIANT} AS appbase
# ==============================
RUN mkdir /entrypoint

COPY --chown=appuser:appuser requirements.txt /app/requirements.txt

RUN apt-install.sh \
        git \
        netcat-openbsd \
        libpq-dev \
        build-essential \
        gdal-bin \
        python3-gdal \
    && pip install -U pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && apt-cleanup.sh build-essential

COPY --chown=appuser:appuser docker-entrypoint.sh /entrypoint/docker-entrypoint.sh
ENTRYPOINT ["/entrypoint/docker-entrypoint.sh"]
EXPOSE 8000/tcp

# ==============================
FROM appbase AS development
# ==============================

COPY --chown=appuser:appuser requirements-dev.txt /app/requirements-dev.txt
RUN apt-install.sh \
        build-essential \
    && pip install --no-cache-dir -r /app/requirements-dev.txt \
    && apt-cleanup.sh build-essential

ENV DEV_SERVER=1

COPY --chown=appuser:appuser . /app/

# django-munigeo municipality importer requires this
RUN mkdir -p /app/data && chgrp -R 0 /app/data && chmod g+w -R /app/data

USER appuser

# ==============================
FROM appbase AS production
# ==============================

COPY --chown=appuser:appuser . /app/

# django-munigeo municipality importer requires this
RUN mkdir -p /app/data && chgrp -R 0 /app/data && chmod g+w -R /app/data

RUN SECRET_KEY="only-used-for-collectstatic" python manage.py collectstatic

USER appuser
