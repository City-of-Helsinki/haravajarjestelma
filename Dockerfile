# ==============================
FROM helsinki.azurecr.io/ubi9/python-39-gdal AS appbase
# ==============================
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
