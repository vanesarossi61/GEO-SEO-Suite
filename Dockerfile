FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md LICENSE ./
COPY geo_seo/ geo_seo/
RUN pip install --no-cache-dir build && python -m build --wheel --outdir /build/wheels .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels /build/wheels/*.whl

FROM python:3.11-slim AS runtime
LABEL maintainer="Vane Rossi <vanesarossi61@gmail.com>"
WORKDIR /app
COPY --from=builder /build/wheels /tmp/wheels
RUN pip install --no-cache-dir --no-index --find-links /tmp/wheels geo-seo-suite && rm -rf /tmp/wheels
RUN groupadd --gid 1000 geoseo && useradd --uid 1000 --gid geoseo --create-home geoseo
RUN mkdir -p /app/config /app/data && chown -R geoseo:geoseo /app
VOLUME ["/app/config", "/app/data"]
USER geoseo
EXPOSE 8000
ENTRYPOINT ["geo-seo"]
CMD ["--help"]
