# Tasks — pdf-validator

> Tareas ordenadas por dependencia, agrupadas en **3 milestones**. Cada tarea mapea a una issue.

## Milestone 1 — Foundation

## Task 1: Bootstrap del proyecto Python (`uv`) + config desde env

**Description:** Inicializar el proyecto con `uv init`, fijar dependencias (`fastapi`, `uvicorn`, `pydantic`, dev: `pytest`, `ruff`), y crear el loader de configuración por variables de entorno.

**Acceptance criteria:**
- [ ] `pyproject.toml` con nombre `pdf-validator`, Python `>=3.12`, dependencias `fastapi`, `uvicorn[standard]`, `pydantic`, `python-multipart` (para multipart) y un logger estructurado (ej. `structlog`)
- [ ] `dev/config.py` con `Settings` (pydantic-settings) leyendo `HTTP_ADDR` (default `:8000`) y `MAX_FILE_SIZE_MB` (default `10`)
- [ ] `.env.example` con ambas variables documentadas

**Verification:**
- [ ] `uv sync` instala sin error
- [ ] Test unitario de `Settings()` con defaults y con env overrides

**Dependencies:** None

**Files likely touched:**
- `pyproject.toml`, `uv.lock`, `.python-version`
- `dev/config.py`, `test/test_config.py`
- `.env.example`

**Estimated scope:** Small (3-4 files)

---

## Task 2: DTOs, Logs a stdout + helpers RFC 9457

**Description:** Aplicar TDD para definir `ValidateResponse` y el enum `Format`. Configurar logging estructurado a `stdout` (Twelve-Factor App). Crear helpers de Problem Details (RFC 9457).

**Acceptance criteria:**
- [ ] Escribir tests unitarios (que fallan inicialmente) para los DTOs y el helper RFC 9457 (TDD).
- [ ] `dev/dto.py`: `Format(str, Enum)` con `PDF = "pdf"`, `MARKDOWN = "markdown"`; `ValidateResponse{original_format: Format, checksum: str}`
- [ ] `dev/problem.py`: `ProblemDetails` (Pydantic) con los 5 campos de ADR-0001; función `problem_response(...)`
- [ ] Configurar logger estructurado en formato JSON hacia `stdout`.

**Verification:**
- [ ] `uv run pytest test/test_dto.py test/test_problem.py`
- [ ] El JSON producido coincide exactamente con los ejemplos del spec (nombres de campo, `Content-Type: application/problem+json`)

**Dependencies:** Task 1

**Files likely touched:**
- `dev/dto.py`, `test/test_dto.py`
- `dev/problem.py`, `test/test_problem.py`

**Estimated scope:** Medium (4 files)

---

## Milestone 2 — Núcleo de clasificación

## Task 3: Checksum SHA-256

**Description:** Portar `calculate_checksum` del monolito aplicando TDD.

**Acceptance criteria:**
- [ ] Escribir tests unitarios (que fallan inicialmente) comprobando el determinismo y casos base.
- [ ] `dev/core/checksum.py`: `calculate_checksum(content: bytes) -> str` (SHA-256 hexdigest)
- [ ] Determinismo: mismo contenido → mismo checksum, dos ejecuciones distintas

**Verification:**
- [ ] `uv run pytest test/test_checksum.py` (incluye caso de determinismo y de contenido vacío)

**Dependencies:** Task 1

**Files likely touched:**
- `dev/core/checksum.py`, `test/test_checksum.py`

**Estimated scope:** Small (2 files)

---

## Task 4: Clasificación PDF (`core/classify.py`)

**Description:** Portar la validación de PDF del monolito mediante TDD, levantando `InvalidFileError` (no `ValueError`).

**Acceptance criteria:**
- [ ] Escribir tests unitarios primero (validos, invalidos, tamaño excedido).
- [ ] `dev/core/errors.py`: `InvalidFileError(Exception)`
- [ ] `dev/core/classify.py`: `classify(content: bytes, filename: str) -> Format`; PDF si `content.startswith(b"%PDF-")`
- [ ] Excede `MAX_FILE_SIZE_MB` → `InvalidFileError` con mensaje equivalente al del monolito
- [ ] Mensajes de error conservan la información útil del monolito (nombre de archivo, tamaño esperado vs. actual)

**Verification:**
- [ ] `uv run pytest test/test_classify.py::test_pdf_valido` y casos de tamaño excedido (Success Criteria 1 y 5 del spec)

**Dependencies:** Task 2, Task 3

**Files likely touched:**
- `dev/core/errors.py`
- `dev/core/classify.py`, `test/test_classify.py`

**Estimated scope:** Small (3 files)

---

## Task 5: Clasificación Markdown

**Description:** Implementar clasificación Markdown mediante TDD.

**Acceptance criteria:**
- [ ] Escribir tests unitarios primero para validación de `.md` y errores de decodificación.
- [ ] `.md` con contenido UTF-8 válido → `Format.MARKDOWN`
- [ ] `.md` con bytes no-UTF-8 → `InvalidFileError`
- [ ] Sin magic bytes de PDF y sin extensión `.md` → `InvalidFileError`
- [ ] El límite `MAX_FILE_SIZE_MB` se aplica también al camino Markdown (decisión de `tasks/plan.md`)
- [ ] No se valida "buen" Markdown más allá de la decodificación (fuera de alcance explícito)

**Verification:**
- [ ] `uv run pytest test/test_classify.py` cubre Success Criteria 2, 3, 4 del spec completos

**Dependencies:** Task 4

**Files likely touched:**
- `dev/core/classify.py`, `test/test_classify.py`

**Estimated scope:** Small (2 files, extiende Task 4)

---

## Checkpoint: Milestone 2 — Núcleo
- [ ] Los 6 casos de clasificación de Success Criteria (1-6) pasan sin FastAPI de por medio
- [ ] Cobertura 100% en `dev/core/`

---

## Milestone 3 — API HTTP + deploy

## Task 6: `POST /validate` (multipart/form-data) + exception handlers RFC 9457

**Description:** Aplicar TDD para montar el endpoint usando `UploadFile` (evitando base64 para minimizar consumo RAM/CPU), delegando la lectura y operaciones intensivas, y devolviendo RFC 9457.

**Acceptance criteria:**
- [ ] `dev/api/router.py`: `POST /validate` con `response_model=ValidateResponse`
- [ ] `dev/api/app.py`: `create_app()` registra el router + los exception handlers de `dev/problem.py`
- [ ] `InvalidFileError` → `400` RFC 9457 con `title: "Archivo inválido"`
- [ ] Payload malformado (JSON inválido, campo faltante) → `400` RFC 9457, no el shape default de FastAPI

**Verification:**
- [ ] `uv run pytest test/test_api.py` con `TestClient`: 200 pdf, 200 markdown, 400 inválido, 400 tamaño, 400 payload malformado — shape RFC 9457 verificado en cada caso de error

**Dependencies:** Task 5, Task 2

**Files likely touched:**
- `dev/api/router.py`, `dev/api/app.py`
- `test/test_api.py`, `test/conftest.py`

**Estimated scope:** Medium (4 files)

---

## Task 7: `GET /health`

**Description:** Endpoint trivial de healthcheck para Docker, sin dependencias.

**Acceptance criteria:**
- [ ] `GET /health` → `200 {"status": "ok"}`, sin tocar `core/` ni ningún estado

**Verification:**
- [ ] `uv run pytest test/test_api.py::test_health`

**Dependencies:** Task 6

**Files likely touched:**
- `dev/api/router.py` (o `dev/api/health.py`), `test/test_api.py`

**Estimated scope:** Small (1-2 files)

---

## Task 8: `main.py` + `Dockerfile` + `docker-compose.yml`

**Description:** Entrypoint que levanta `uvicorn` con la app, e imagen Docker sin exposición al host, conectada a `fast_pdf_network`.

**Acceptance criteria:**
- [ ] `dev/main.py`: arma `create_app()` y llama `uvicorn.run(...)` leyendo `HTTP_ADDR` de `Settings`
- [ ] `Dockerfile`: `python:3.12-slim`, `uv sync --frozen --no-dev`, usuario no-root, sin `ports` expuestos
- [ ] `docker-compose.yml`: sin labels de Traefik, `networks: [fast_pdf_network]` (externa), sin `ports:` al host
- [ ] `HEALTHCHECK` de Docker contra `GET /health`

**Verification:**
- [ ] `docker build .` compila
- [ ] `docker compose config` valida
- [ ] `docker run` local + `curl` interno a `/health` y `/validate` responde correctamente

**Dependencies:** Task 7

**Files likely touched:**
- `dev/main.py`
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`

**Estimated scope:** Medium (4 files)

---

## Checkpoints

### Checkpoint: Milestone 1 — Foundation (tras Tasks 1-2)
- [ ] `uv sync` y `ruff check .` limpios; DTOs alineados con el contrato de `pdf-main`

### Checkpoint: Milestone 2 — Núcleo (tras Tasks 3-5)
- [ ] Los 6 casos de clasificación del spec pasan sin FastAPI; cobertura 100% en `core/`

### Checkpoint: Milestone 3 — Complete (tras Tasks 6-8)
- [ ] Todos los success criteria del spec verificados end-to-end (incluye Docker)
- [ ] `ruff check .`, `ruff format --check .`, `uv run pytest` limpios
- [ ] Listo para REVIEW
