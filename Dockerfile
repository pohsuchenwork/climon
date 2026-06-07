# Image for the climon online server. The server never renders sprites, so this
# image only needs the package and its runtime dependencies (no chafa, no assets
# rendering). It binds 0.0.0.0:8080 so the Fly proxy can route wss traffic to it.
FROM python:3.13-slim

# CLIMON_PORT is the local default; a host that injects PORT (Render) overrides it.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    CLIMON_HOST=0.0.0.0 \
    CLIMON_PORT=8080

WORKDIR /app

# Copy only what the hatchling build needs (pyproject reads the version from the
# package and the readme/license from these files), then install the package.
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

EXPOSE 8080
CMD ["python", "-m", "climon.server"]
