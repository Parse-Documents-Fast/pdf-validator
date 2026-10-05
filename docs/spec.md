# Spec: pdf-validator

**Estado:** Propuesto

## Objective

`pdf-validator` es el servicio de **clasificación y validación de formato** del sistema *Parse Documents Fast*. Recibe bytes crudos de un archivo (PDF o Markdown) y responde con su clasificación (`pdf` | `markdown`) más su checksum SHA-256, o rechaza el archivo si no es ninguno de los dos formatos soportados. Es el primer paso del flujo de subida en `pdf-main` (ADR-0004): su respuesta gatilla, en el mismo request, a qué servicio llama `pdf-main` después (`pdf-extractor` vía cola, o persistencia directa).

No extrae contenido, no convierte, no persiste, no decide duplicados (eso lo hace `pdf-main` contra `pdf-persistence` con el checksum que este servicio calcula). Es el servicio más simple del sistema: sin estado, sin dependencias externas (ni Mongo, ni Redis, ni otros servicios), una sola llamada de entrada y una de salida.

**Usuario:** únicamente `pdf-main`, vía HTTP síncrono (ADR-0004 — su resultado gatilla una decisión de ruteo en el mismo request).

**Éxito:** un PDF válido responde `200` con `original_format: "pdf"`; un Markdown válido responde `200` con `original_format: "markdown"`; cualquier otro contenido responde `400` RFC 9457.

---

## Alcance (qué hace y qué NO hace)

### Hace

1. Clasificar el contenido recibido como `pdf` o `markdown`, en ese orden de chequeo:
   - **PDF:** el contenido comienza con los magic bytes `%PDF-` (lógica portada tal cual del monolito, `validate_pdf_bytes`).
   - **Markdown:** el archivo no es un PDF válido, su nombre termina en `.md`, y el contenido decodifica como UTF-8 válido.
2. Validar el tamaño máximo (`MAX_FILE_SIZE_MB`) sobre el contenido, para ambos formatos por igual.
3. Calcular el checksum SHA-256 del contenido binario (lógica portada tal cual del monolito, `calculate_checksum`), independientemente del formato.
4. Responder `200` con `{ original_format, checksum }`, o `400` RFC 9457 si el archivo no es válido en ningún formato o supera el tamaño máximo.

### No hace

- **No** verifica estructura interna de un PDF (páginas, objetos, si es extraíble) — eso es trabajo de `pdf-extractor`.
- **No** verifica sintaxis real de Markdown (headers bien formados, etc.) — "decodifica como UTF-8" es la única condición; el resto es responsabilidad de quien lo escribió.
- **No** detecta duplicados — solo calcula el checksum; la comparación contra lo ya persistido la hace `pdf-main` contra `pdf-persistence`.
- **No** persiste nada ni mantiene estado entre requests.
- **No** toca disco en ningún punto — todo en memoria (restricción del profesor, igual que el resto del sistema).

---

## Tech Stack

| Componente | Elección | Justificación |
|---|---|---|
| Lenguaje | Python 3.12+ | Continuidad directa con el monolito: la lógica a portar (`validate_pdf_bytes`, `calculate_checksum`) ya está escrita y probada en Python — reescribirla en otro lenguaje no aporta nada en un servicio sin necesidad de concurrencia pesada (a diferencia de `pdf-main`, que sí la necesita). |
| Framework | FastAPI | Mismo framework del monolito; sus exception handlers son el mecanismo natural para RFC 9457 (ADR-0001 lo menciona explícitamente como opción para Python). |
| Validación de request | FastAPI + Pydantic v2 | Pydantic modela `ValidateRequest` (`filename`, `content_base64`) y `ValidateResponse`. El request es JSON con el binario en base64 (ADR-0002, `pdf-docs/contracts/contracts-validator.md`). |
| Observabilidad | logging / structlog | Logs estructurados a stdout cumpliendo Twelve-Factor App, clave para la observabilidad en pruebas de carga. |
| Gestor de paquetes | `uv` | Igual que el monolito y que el resto de servicios Python del sistema. |
| Servidor ASGI | `uvicorn` | Estándar para FastAPI. |
| Testing | `pytest` | Igual que el monolito. |
| MongoDB / Redis / HTTP clients a otros servicios | *ninguno* | Este servicio no tiene dependencias externas — es una función pura expuesta por HTTP. |

**Módulo/paquete:** el código vive bajo `dev/`, mismo nombre de carpeta raíz que usa el monolito (`pdf-extractext`), para minimizar la fricción de cualquiera del equipo que ya conoce esa convención.

---

## Commands

```bash
# Instalar dependencias
uv sync

# Test
uv run pytest

# Lint / formato
uv run ruff check .
uv run ruff format --check .

# Dev (run local)
uv run uvicorn dev.api.app:app --reload --port 8000
```

---

## Project Structure

```
dev/
  __init__.py
  main.py              → entrypoint: uvicorn.run(create_app())
  config.py             → Settings (env vars): HTTP_ADDR, MAX_FILE_SIZE_MB
  problem.py            → RFC 9457: ProblemDetails + exception handlers FastAPI
  dto.py                → Pydantic: ValidateRequest, ValidateResponse, Format (enum "pdf"|"markdown")
  core/                  → NÚCLEO puro (sin HTTP), ADR-0004
    __init__.py
    errors.py            → InvalidFileError (excepción de dominio, sin conocimiento de HTTP)
    checksum.py           → calculate_checksum(content: bytes) -> str
    classify.py           → classify(content: bytes, filename: str) -> Format  (levanta InvalidFileError)
  api/                   → ADAPTADOR HTTP (delgado), ADR-0004
    __init__.py
    app.py                → create_app(): registra router + exception handlers
    router.py              → POST /validate
docs/
  spec.md                → este documento
  plan-pdf-validator.md
  standards/              → ADRs referenciadas (copia de pdf-docs)
tasks/
  plan.md
  todo.md
test/
  conftest.py
  test_checksum.py
  test_classify.py
  test_api.py
```

La separación `core/` (puro) vs `api/` (adaptador) sigue ADR-0004 aunque el servicio sea chico: el núcleo (`classify`, `calculate_checksum`) no importa nada de FastAPI ni conoce HTTP, se testea directo sin `TestClient`; `api/router.py` es la única capa que traduce el DTO del wire a la llamada al núcleo y el resultado (o `InvalidFileError`) a una respuesta HTTP.

---

## Code Style

Mismo estilo que el monolito: type hints, docstrings en español, excepciones tipadas heredando de una base común (acá, todo error de dominio es `InvalidFileError`, no `ValueError` genérico — a diferencia del monolito, donde varias excepciones heredaban de `ValueError`; acá no hace falta esa jerarquía porque hay un solo tipo de error posible).

```python
# dev/core/errors.py — núcleo puro, sin HTTP.
class InvalidFileError(Exception):
    """El contenido no es un PDF ni un Markdown válido, o supera el tamaño máximo."""


# dev/core/classify.py — núcleo puro, sin HTTP.
def classify(content: bytes, filename: str) -> Format:
    if content.startswith(PDF_MAGIC_BYTES):
        _check_size(content)
        return Format.PDF

    if filename.lower().endswith(".md"):
        _check_utf8(content)
        _check_size(content)
        return Format.MARKDOWN

    raise InvalidFileError(
        f"El archivo '{filename}' no es un PDF ni un Markdown válido."
    )
```

```python
# dev/api/router.py — adaptador HTTP, delgado.
@router.post("/validate", response_model=ValidateResponse)
async def validate(req: ValidateRequest) -> ValidateResponse:
    # Se decodifica el base64 (400 si es inválido) y luego se procesa en el threadpool para no bloquear el event loop.
    content = base64.b64decode(req.content_base64, validate=True)
    try:
        # Se puede delegar a un threadpool si classify/checksum son pesados
        fmt = classify(content, req.filename)
        checksum = calculate_checksum(content)
    except InvalidFileError as e:
        raise ProblemHTTPException(400, "Archivo inválido", str(e))
    return ValidateResponse(original_format=fmt, checksum=checksum)
```

Convenciones:
- El núcleo (`core/`) nunca importa `fastapi`, `starlette` ni conoce el wire — recibe y devuelve tipos Python puros (`bytes`, `str`, el enum `Format`).
- Todo error de negocio es `InvalidFileError`; `api/router.py` es el único lugar que lo traduce a RFC 9457.
- `MAX_FILE_SIZE_MB` se aplica igual a ambos formatos (decisión de diseño, ver Open Questions en `tasks/plan.md`).

---

## Testing Strategy

- Framework: `pytest`.
- Niveles:
  - **Unit (núcleo):** `classify()` y `calculate_checksum()` contra bytes construidos a mano — sin FastAPI, sin HTTP. Casos: PDF válido, PDF que excede tamaño, Markdown válido (`.md` + UTF-8), Markdown con extensión pero bytes no-UTF-8, archivo sin magic bytes y sin extensión `.md`, archivo `.md` vacío.
  - **API (adaptador):** `TestClient` de FastAPI contra `POST /validate`. Casos: 200 pdf, 200 markdown, 400 inválido (shape RFC 9457 completo), 400 por tamaño, `422` de Pydantic (payload malformado) también traducido a RFC 9457 — **no** el shape default de FastAPI.
- Cobertura objetivo: 100% en `core/` (es la lógica que realmente importa acá); `api/` cubierto por los casos de status code de arriba, sin perseguir cobertura de líneas.
- No hace falta `test/stubs/` (a diferencia de `pdf-main`): este servicio no tiene downstreams que mockear.

---

## DTOs (contrato de wire — snake_case, ADR-0002)

**Fuente de verdad:** `pdf-main` + `pdf-docs/contracts/contracts-validator.md`.

**Request (POST /validate):** JSON
```json
{
  "filename": "informe.pdf",
  "content_base64": "JVBERi0xLjQKJcOkw7zDtsO4Cg=="
}
```

**Response (200 OK):**
```jsonc
{
  "original_format": "pdf",           // "pdf" | "markdown"
  "checksum": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"
}
```

Error → RFC 9457 (ADR-0001), `Content-Type: application/problem+json`:

```jsonc
{
  "type": "about:blank",
  "title": "Archivo inválido",
  "status": 400,
  "detail": "El archivo 'foto.jpg' no es un PDF ni un Markdown válido.",
  "instance": "/validate"
}
```

---

## Endpoints

| Método | Path | Éxito | Errores (RFC 9457) |
|---|---|---|---|
| `POST` | `/validate` | `200` `ValidateResponse` | `400` archivo inválido o excede tamaño máximo |
| `GET` | `/health` | `200` `{"status":"ok"}` | — |

`GET /health` no es parte del contrato con `pdf-main` (que solo llama a `/validate`) — se agrega por práctica operativa estándar (healthcheck de Docker). Se puede sacar del alcance si el equipo lo prefiere.

---

## Configuración (variables de entorno)

| Variable | Default | Descripción |
|---|---|---|
| `HTTP_ADDR` | `:8000` | Puerto interno de escucha. Mismo nombre de variable que `pdf-main` (ADR de convención de nombres implícita: cualquiera que lea las tablas de env vars de varios repos del sistema encuentra el mismo nombre para "en qué puerto escucha"), aunque el mecanismo de binding en Python/uvicorn difiera del de Go. |
| `MAX_FILE_SIZE_MB` | `10` | Igual valor y nombre que en el monolito y que en `pdf-main`. |

No hay `MONGO_URI`, ni URLs de otros servicios, ni streams de Redis — este servicio no habla con nada más.

**Traefik:** `pdf-validator` **no** declara labels de Traefik ni rutas públicas — es interno, alcanzable solo dentro de `fast_pdf_network` por su nombre de servicio Docker (`http://pdf-validator:8000`, el mismo valor que `pdf-main` ya tiene como default de `VALIDATOR_URL` en su propio spec).

---

## Boundaries

- **Always:**
  - `ruff check` + `ruff format --check` + `uv run pytest` antes de commit.
  - JSON tags `snake_case` (ADR-0002).
  - Errores al cliente en RFC 9457, incluidos los `422` que Pydantic generaría por default (ADR-0001 — no alcanza con el shape default de FastAPI).
  - Núcleo (`core/`) sin conocimiento de HTTP (ADR-0004).
  - Todo en RAM: nunca escribir a disco, ni siquiera temporalmente.

- **Ask first:**
  - Cambiar el nombre de un campo de `ValidateRequest`/`ValidateResponse` (contrato compartido, fuente de verdad en `pdf-main`).
  - Agregar una dependencia nueva al `pyproject.toml`.
  - Cambiar el criterio de clasificación (orden de chequeo PDF→Markdown, o el criterio de "Markdown válido").
  - Aplicar un límite de tamaño distinto por formato (hoy es el mismo `MAX_FILE_SIZE_MB` para ambos — ver Open Questions).

- **Never:**
  - Commitear secretos / `.env`.
  - Escribir archivos temporales en disco.
  - Hablar con Mongo, Redis, u otro servicio del sistema — este servicio no tiene downstreams.
  - Exponer puerto al host ni declarar labels de Traefik.
  - Verificar contenido más allá de "decodifica" (estructura de PDF, sintaxis de Markdown) — eso es explícitamente fuera de alcance (`docs/plan-pdf-validator.md`).

---

## Success Criteria

1. `POST /validate` con un PDF válido (`%PDF-...`) responde `200` con `original_format: "pdf"` y el checksum SHA-256 correcto.
2. `POST /validate` con un `.md` válido en UTF-8 responde `200` con `original_format: "markdown"` y su checksum.
3. `POST /validate` con contenido que no empieza con `%PDF-` y cuyo `filename` no termina en `.md` responde `400` RFC 9457.
4. `POST /validate` con un `.md` cuyo contenido no decodifica como UTF-8 responde `400` RFC 9457.
5. `POST /validate` con contenido (de cualquier formato) que supera `MAX_FILE_SIZE_MB` responde `400` RFC 9457.
6. El mismo contenido, subido dos veces, produce el mismo checksum (determinismo — necesario para que `pdf-main`/`pdf-persistence` detecten duplicados corractamente).
7. Un payload malformado (falta `filename`/`content_base64`, o base64 inválido) responde `400` en RFC 9457, no el shape default de validación de FastAPI.
8. Logs en formato JSON son emitidos a `stdout` (Twelve-Factor App).
8. `GET /health` responde `200` sin autenticación ni dependencias.
9. `ruff check .`, `ruff format --check .` y `uv run pytest` pasan limpios.
10. `docker compose config` valida; el contenedor no expone puertos al host y se conecta a `fast_pdf_network`.

---

## Coordinación con otros repos

1. **`pdf-main`** es la fuente de verdad del contrato (`ValidateRequest`/`ValidateResponse`, path `/validate`) — cualquier cambio de campo se coordina ahí primero (ya commiteado en `internal/dto/validator.go` y `internal/dto/endpoints.go`).
2. **`pdf-infra`** provee la red `fast_pdf_network` que este servicio declara como externa en su `docker-compose.yml` — sin rutear nada a través de Traefik.
3. **`pdf-docs`** aún no tiene ADR-0005 promovida al repo central (solo está en la copia local de `pdf-main`) — no afecta a este servicio (Markdown como canónico es una decisión de persistencia/extracción, no de validación), pero vale la pena que el equipo lo sincronice en algún momento.
