# Implementation Plan: pdf-validator

## Overview

Construir `pdf-validator`, el servicio de clasificación y validación de formato del sistema *Parse Documents Fast*, en Python/FastAPI. Recibe un archivo binario mediante `multipart/form-data` (evitando base64 para optimizar CPU y memoria durante las pruebas de carga extrema), clasifica el contenido como `pdf` o `markdown` (portando `validate_pdf_bytes`/`calculate_checksum` del monolito para el caso PDF, y agregando el chequeo de Markdown), y responde `{original_format, checksum}` o `400` RFC 9457. Sin estado, sin downstreams — el servicio más chico del sistema.

**Seguimiento:** las tareas de abajo son la fuente de las issues, mapeadas 1:1 a GitHub Issues, agrupadas en **3 milestones**.

## Architecture Decisions

1. **Núcleo puro (`core/`) separado del adaptador HTTP (`api/`)** — ADR-0004, aplicado aunque el servicio sea chico: `classify()` y `calculate_checksum()` no conocen FastAPI ni el wire (`multipart/form-data`), se testean sin `TestClient`. El desarrollo debe hacerse siguiendo **TDD (Test-Driven Development)** de forma estricta.
2. **Un solo tipo de excepción de dominio (`InvalidFileError`)** — a diferencia del monolito (que tenía `PdfValidationError`, `PdfNotFoundError`, `DuplicatePdfError` porque ese módulo hacía más cosas), acá solo hay un modo de fallo posible: el archivo no es válido. No hace falta jerarquía de excepciones.
3. **`MAX_FILE_SIZE_MB` aplica igual a PDF y Markdown** — el monolito solo tenía PDFs, así que este es un criterio nuevo. Se documenta como decisión explícita en el spec (ver Open Questions) en vez de dejarlo implícito.
4. **Sin `test/stubs/`** — a diferencia de `pdf-main`, este servicio no tiene ningún downstream que mockear; sus tests son directos contra el núcleo o contra `TestClient`.
5. **Reutilización literal del monolito** — `_check_magic_bytes` y `calculate_checksum` se portan con la misma lógica y los mismos mensajes de error (adaptados al nuevo tipo de excepción), no se reinventan (`docs/plan-pdf-validator.md`, ya aprobado).
6. **`ruff` en vez de manual style-check** — el monolito no tenía un linter configurado explícitamente; se agrega acá porque es un repo nuevo y el costo de introducirlo es mínimo al empezar de cero.

## Task List

### Milestone 1 — Foundation

- [ ] Task 1: Bootstrap del proyecto Python (`uv`) + config desde env
- [ ] Task 2: DTOs (Pydantic para Response) + helpers RFC 9457 + Logger a stdout

### Checkpoint: Foundation
- [ ] `uv run pytest` corre (vacío o con tests triviales), `ruff check .` limpio
- [ ] Los DTOs de respuesta serializan con los nombres de campo exactos del contrato (`original_format`, `checksum`)

### Milestone 2 — Núcleo de clasificación

- [ ] Task 3: Checksum SHA-256 (`core/checksum.py`)
- [ ] Task 4: Clasificación PDF (`core/classify.py`, portando `validate_pdf_bytes`)
- [ ] Task 5: Clasificación Markdown (extensión `.md` + UTF-8) sobre el mismo `classify()`

### Checkpoint: Núcleo
- [ ] `classify()` cubre los 6 casos de Success Criteria 1-6 del spec, testeado sin FastAPI
- [ ] Cobertura 100% en `core/`

### Milestone 3 — API HTTP + deploy

- [ ] Task 6: `POST /validate` + exception handlers RFC 9457 (incluye 422 de Pydantic)
- [ ] Task 7: `GET /health`
- [ ] Task 8: `main.py` (entrypoint) + `Dockerfile` + `docker-compose.yml`

### Checkpoint: Complete
- [ ] Todos los success criteria del spec verificados
- [ ] `ruff check .` y `ruff format --check .` limpios; `uv run pytest` pasa
- [ ] `docker compose config` valida; sin puertos expuestos al host; conectado a `fast_pdf_network`
- [ ] Listo para REVIEW

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Drift del contrato con `pdf-main` | High | Se cambió el contrato a `multipart/form-data` para evitar cuellos de botella por decodificación base64. Coordinar con `pdf-main` para alinear este requerimiento de optimización. |
| Pydantic devuelve su shape de error default (422) en vez de RFC 9457 ante payload malformado | Med | Exception handler explícito para `RequestValidationError` en Task 6, cubierto en Success Criteria 7 |
| Ambigüedad en si el límite de tamaño debe ser el mismo para PDF y Markdown | Low | Resuelto en este plan (mismo límite); documentado como decisión explícita, no implícita |
| ADR-0005 (Markdown canónico) no está aún en `pdf-docs` central | Low | No afecta a este servicio directamente; señalado en Coordinación del spec para que el equipo lo sincronice |

## Open Questions

- Ninguna bloqueante. La única decisión de diseño no dictada por el plan original (límite de tamaño compartido entre formatos) queda resuelta y documentada en el spec — confirmar con el equipo si se prefiere un límite distinto para Markdown antes de cerrar Milestone 2.
