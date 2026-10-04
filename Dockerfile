FROM python:3.12-slim

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Setup working directory
WORKDIR /app

# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app

# Copy dependency files
COPY pyproject.toml README.md .
# Do not copy uv.lock since we removed it from version control in Issue 4, uv will resolve it.
# Actually, since it's a microservice, if there was a lock file we would use `uv sync --frozen`.
# Since there is no uv.lock we use `uv sync`.
RUN uv sync --no-dev

# Copy application source
COPY dev/ dev/

# Change to non-root user
USER appuser

# Healthcheck against /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uv", "run", "python", "-m", "dev.main"]
