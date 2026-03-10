# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY geo_seo/ ./geo_seo/

RUN pip install --no-cache-dir build && \
    python -m build --wheel --outdir /wheels

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

LABEL maintainer="Vane Rossi <vanesarossi61@gmail.com>"
LABEL description="GEO-SEO Suite v2.0 - Professional GEO/SEO optimization toolkit"

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels

RUN useradd --create-home --shell /bin/bash geoseo
USER geoseo

EXPOSE 8000

ENTRYPOINT ["geo-seo"]
CMD ["serve"]
