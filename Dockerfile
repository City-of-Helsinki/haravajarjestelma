# ==============================
FROM helsinkitest/python:3.9-slim as appbase
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
    && pip install -U pip \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && apt-cleanup.sh build-essential

COPY --chown=appuser:appuser docker-entrypoint.sh /entrypoint/docker-entrypoint.sh
ENTRYPOINT ["/entrypoint/docker-entrypoint.sh"]

# ==============================
FROM appbase as development
# ==============================

COPY --chown=appuser:appuser requirements-dev.txt /app/requirements-dev.txt
RUN apt-install.sh \
        build-essential \
    && pip install --no-cache-dir -r /app/requirements-dev.txt \
    && apt-cleanup.sh build-essential

ENV DEV_SERVER=1

COPY --chown=appuser:appuser . /app/

USER appuser
EXPOSE 8085/tcp

# ==============================
FROM appbase as production
# ==============================

COPY --chown=appuser:appuser . /app/

RUN SECRET_KEY="only-used-for-collectstatic" python manage.py collectstatic

USER appuser
EXPOSE 8000/tcp
