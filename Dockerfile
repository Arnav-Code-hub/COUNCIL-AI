FROM node:22-bookworm-slim AS web
WORKDIR /build
COPY web/package*.json ./
RUN --mount=type=secret,id=ca_bundle \
    if [ -f /run/secrets/ca_bundle ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/ca_bundle; fi \
    && npm ci
COPY web/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml requirements.lock ./
COPY council/ ./council/
RUN --mount=type=secret,id=ca_bundle \
    if [ -f /run/secrets/ca_bundle ]; then export PIP_CERT=/run/secrets/ca_bundle SSL_CERT_FILE=/run/secrets/ca_bundle; fi \
    && pip install --no-cache-dir -r requirements.lock && pip install --no-cache-dir --no-deps .
COPY --from=web /build/dist ./web/dist
RUN useradd --create-home council && mkdir /data && chown council:council /data
USER council
ENV COUNCIL_DATA_DIR=/data
EXPOSE 8090
# Hosts such as Render assign the listening port through PORT; local Docker keeps 8090.
CMD ["sh","-c","exec uvicorn council.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8090} --workers 1"]
