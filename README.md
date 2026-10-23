# PDF Validator Microservice

Microservicio asíncrono para la validación perimetral de archivos (PDF y Markdown) y cálculo de hash criptográfico (SHA-256), diseñado bajo el patrón *Fast Path* para evitar el bloqueo del monolito principal (pdf-main).

## Características Principales

- **Validación Rápida:** Detección de *Magic Bytes* (%PDF-) y chequeo de decodificación de archivos Markdown.
- **Rendimiento:** Escrito en **Python 3.12** utilizando **FastAPI** y operaciones delegadas a un *threadpool* (nyio.to_thread) para no bloquear el *Event-Loop*.
- **Integración Base64:** Ingesta de archivos mediante JSON en formato ase64 para mantener compatibilidad con el contrato de pdf-main.
- **Estándares:** Todas las respuestas de error respetan rígidamente el estándar **RFC 9457** (Problem Details for HTTP APIs).
- **Hardening Docker:** Construido en imagen de usuario *non-root* (ppuser) y aislado exclusivamente en la red de backend de docker ast_pdf_network.

## Endpoints

- POST /validate: Recibe un JSON (DocumentContent) con los campos content_base64 y ilename. Retorna el tipo detectado (pdf o markdown) y su checksum SHA-256. En caso de fallar, responde con HTTP 400 y el JSON tipo RFC 9457.
- GET /health: Endpoint trivial expuesto para propósitos del Docker HEALTHCHECK.

## Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| HTTP_ADDR | Host y puerto donde servirá Uvicorn. | :8000 |
| LOG_LEVEL | Nivel de verbosidad del logger. | INFO |
| PDF_VALIDATOR_REPLICAS | Número de réplicas a instanciar en Docker Compose. | 1 |

## Comandos de Desarrollo Locales

El repositorio utiliza [uv](https://github.com/astral-sh/uv) como gestor empaquetador ultrarrápido y para la gestión de dependencias en espacio de usuario.

```powershell
# Sincronizar el entorno y dependencias (equivalente a pip install)
uv sync

# Iniciar la aplicación en modo desarrollo
uv run python -m dev.main

# Ejecutar suite de pruebas TDD completa (Pytest)
uv run pytest test/

# Ejecutar el linter y corrector de estilo (Ruff)
uv run ruff check .
uv run ruff format .
```

## Ejecución por Docker

```bash
# Construye la imagen e inicia el contenedor con 1 réplica por defecto
docker compose up -d --build

# Escalar horizontalmente (ej: 5 réplicas)
PDF_VALIDATOR_REPLICAS=5 docker compose up -d
```
> **Nota:** El microservicio no expone puertos al *host local* para permitir escalado horizontal sin colisión de puertos. `pdf-main` accede a él mediante balanceo DNS interno en la red `fast_pdf_network`.

## Logging Estructurado (ADR-0007)

Los logs se emiten a `stdout` en formato JSON de una sola línea por evento, cumpliendo el factor XI de Twelve-Factor App y el estándar del proyecto:

```json
{"time":"2026-10-23T20:10:00.123Z","level":"INFO","service":"pdf-validator","msg":"file validated","checksum":"a94a8fe5...","original_format":"pdf","size_bytes":1024,"duration_ms":3.21}
{"time":"2026-10-23T20:10:00.125Z","level":"WARN","service":"pdf-validator","msg":"validation failed","reason":"unsupported format"}
```

- **Niveles:** `DEBUG`, `INFO`, `WARN`, `ERROR` (configurable mediante `LOG_LEVEL`, default `INFO`).
- **Privacidad:** Nunca se registran contenidos ni bytes de los archivos en memoria; únicamente metadatos (`checksum`, `original_format`, `size_bytes`, `duration_ms`, `reason`).


