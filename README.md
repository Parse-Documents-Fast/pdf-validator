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

## Comandos de Desarrollo Locales

El repositorio utiliza [uv](https://github.com/astral-sh/uv) como gestor empaquetador ultrarrápido y para la gestión de dependencias en espacio de usuario.

`powershell
# Sincronizar el entorno y dependencias (equivalente a pip install)
uv sync

# Iniciar la aplicación en modo desarrollo
uv run python -m dev.main

# Ejecutar suite de pruebas TDD completa (Pytest)
uv run pytest test/

# Ejecutar el linter y corrector de estilo (Ruff)
uv run ruff check .
uv run ruff format .
`

## Ejecución por Docker

`ash
# Construye la imagen e inicia el contenedor de manera aislada
docker compose up -d --build
`
> **Nota:** El microservicio no expone puertos al *host local*. Deberá acceder a él a través de otro servicio conectado a la red ast_pdf_network.
