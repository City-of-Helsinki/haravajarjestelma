# ==============================
FROM registry.access.redhat.com/ubi9/python-39 as appbase
# ==============================
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

USER root

COPY requirements.txt .

# Install general build dependencies
RUN dnf update -y && dnf install -y \
    gettext \
    gcc \
    make \
    tar \
    python3-devel \
    cmake \
    && pip install -U pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Install PROJ from source
RUN mkdir -p /proj \
    && curl -L https://github.com/OSGeo/proj/archive/refs/tags/9.4.1.tar.gz | tar xz -C /proj \
    && cd /proj/PROJ-9.4.1 \
    && mkdir build \
    && cd build \
    && cmake .. \
    && make \
    && make install \
    && ldconfig \
    && rm -rf /proj

# Install GDAL from source
RUN mkdir -p /gdal \
    && curl -L https://github.com/OSGeo/gdal/archive/refs/tags/v3.5.1.tar.gz | tar xz -C /gdal \
    && cd /gdal/gdal-3.5.1 \
    && mkdir build \
    && cd build \
    && cmake .. \
    && make \
    && make install \
    && ldconfig \
    && rm -rf /gdal

# Install GEOS from source
RUN mkdir -p /geos \
    && curl -L https://download.osgeo.org/geos/geos-3.12.2.tar.bz2 -o /geos/geos.tar.bz2 \
    && tar xjf /geos/geos.tar.bz2 -C /geos \
    && cd /geos/geos-3.12.2 \
    && mkdir build \
    && cd build \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr/local .. \
    && make \
    && make install \
    && ldconfig \
    && rm -rf /geos

# Set LD_LIBRARY_PATH to include the directory where GDAL libraries are installed
ENV LD_LIBRARY_PATH="/usr/local/lib64:$LD_LIBRARY_PATH"

# TODO Needed?
ENV GEOS_LIBRARY_PATH="/usr/local/lib/libgeos_c.so"

# Clean up
RUN dnf clean all && rm -rf /var/cache/dnf

ENTRYPOINT ["/app/docker-entrypoint.sh"]

# ==============================
FROM appbase AS development
# ==============================

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

ENV DEV_SERVER=True

COPY . .

RUN mkdir -p /app/media && chmod -R g+w /app/media && chgrp -R root /app/media

USER default
EXPOSE 8000/tcp

# ==============================
FROM appbase AS staticbuilder
# ==============================

ENV VAR_ROOT=/app
COPY . /app

# ==============================
FROM appbase AS production
# ==============================

COPY --from=staticbuilder /app/static /app/static
COPY . .

RUN mkdir -p /app/media && chmod -R g+w /app/media && chgrp -R root /app/media

USER default
EXPOSE 8000/tcp
