# ADR-0001: Formato estándar de errores HTTP (RFC 9457)

**Estado:** Aceptado

## Contexto

El sistema se compone de varios microservicios (Go y Python, potencialmente más lenguajes a futuro), cada uno exponiendo o consumiendo errores HTTP. Sin un formato común, cada servicio termina devolviendo errores con una forma distinta (`{"error": "..."}`, `{"detail": "..."}`, `{"message": "...", "code": ...}`), obligando a cualquier cliente (el CLI, otro microservicio, el gateway) a conocer la forma particular de cada uno para poder parsearlo.

Necesitamos un contrato de error único, independiente del lenguaje que lo genera.

## Decisión

Todo error HTTP devuelto por cualquier microservicio del sistema sigue **RFC 9457 (Problem Details for HTTP APIs)**, con `Content-Type: application/problem+json`.

Campos obligatorios:

| Campo | Tipo | Descripción |
|---|---|---|
| `type` | string (URI) | Identificador del tipo de error. Si no hay una URI real de documentación, usar `about:blank`. |
| `title` | string | Resumen corto y estable del tipo de error (no varía entre instancias del mismo error). |
| `status` | int | El código de estado HTTP, repetido acá para que el body sea autocontenido. |
| `detail` | string | Explicación específica de esta ocurrencia puntual. |
| `instance` | string (URI) | El path del request que produjo el error. |

Campos adicionales específicos del dominio pueden agregarse como extensiones (ver ejemplo de duplicado más abajo), siempre que no pisen los cinco nombres reservados de arriba.

### Ejemplo — recurso no encontrado

```json
{
  "type": "about:blank",
  "title": "PDF no encontrado",
  "status": 404,
  "detail": "No existe un PDF con ID 'abc123'",
  "instance": "/api/pdfs/abc123"
}
```

### Ejemplo — con extensión propia (duplicado detectado)

```json
{
  "type": "about:blank",
  "title": "Documento duplicado",
  "status": 409,
  "detail": "Este documento ya fue subido anteriormente",
  "instance": "/api/pdfs",
  "existing_id": "665f1a2b3c4d5e6f7a8b9c0d"
}
```

### Ejemplo — validación fallida

```json
{
  "type": "about:blank",
  "title": "Archivo inválido",
  "status": 400,
  "detail": "El archivo 'foto.jpg' no es un PDF válido. Se esperaba que comenzara con '%PDF-'.",
  "instance": "/api/pdfs"
}
```

## Consecuencias

**Positivas:**
- Cualquier cliente (CLI, otro microservicio, el gateway) parsea errores de la misma forma sin importar en qué lenguaje esté escrito el servicio que los generó.
- El formato es un estándar IETF real, no una convención inventada para este proyecto — hay bibliotecas ya hechas para ambos lenguajes (`problem-details` en Python vía FastAPI/Starlette exception handlers; paquetes equivalentes en Go).
- Los campos son autoexplicativos y extensibles sin romper el contrato base.

**Negativas / a tener en cuenta:**
- Cada servicio necesita un exception handler central que traduzca sus excepciones de dominio a este formato — no alcanza con devolver el string de la excepción tal cual (como se hacía antes en el monolito con `HTTPException(status_code=404, detail=str(e))`).
- Hay que definir, servicio por servicio, un `title` estable por tipo de error (no debe cambiar entre distintas ocurrencias del mismo tipo de error).

## Alternativas descartadas

- **Formato propio ad-hoc** (`{"error": "...", "code": "..."}`): más simple de escribir al principio, pero cada servicio termina inventando su propia variante con el tiempo, exactamente el problema que este ADR busca evitar.
- **Devolver solo el mensaje de texto** (como hacía el monolito original): pierde toda estructura machine-readable — un cliente no puede diferenciar programáticamente un tipo de error de otro sin parsear texto libre.
