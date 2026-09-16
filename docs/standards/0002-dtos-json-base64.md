# ADR-0002: DTOs en JSON, contenido binario codificado en base64

**Estado:** Aceptado

## Contexto

Los microservicios necesitan intercambiar el contenido binario del PDF (por ejemplo, del servicio que recibe el upload hacia `pdf-extractor`), respetando la restricción del profesor de manejar todo en RAM, sin tocar disco en ningún punto del proceso.

El transporte elegido entre servicios es JSON — tanto en mensajes de cola (Redis) como en llamadas HTTP directas. JSON es un formato de texto: no puede representar bytes binarios crudos dentro de un string sin corromperlos (los bytes de un PDF incluyen secuencias que no son UTF-8 válido).

Además, los servicios están en distintos lenguajes (Go, Python), cada uno con su propia convención de nombres (`snake_case` en Python, `PascalCase`/`camelCase` en Go) — hace falta un contrato de datos que no dependa de la convención interna de ningún lenguaje en particular.

## Decisión

Toda comunicación entre servicios usa **DTOs en JSON**. Cualquier contenido binario (los bytes del PDF) va codificado en **base64** dentro de un campo string del DTO — nunca se escribe a un archivo temporal ni se pasa por ningún medio que toque disco.

El **nombre de los campos en el JSON es fijo en `snake_case`**, independientemente de la convención interna de cada lenguaje. Cada servicio mapea el JSON a sus propias estructuras internas con la convención que le sea natural (un `struct` en Go con tags `json:"pdf_id"`, un modelo Pydantic en Python que ya usa `snake_case` de forma nativa).

### Ejemplo — job de extracción encolado

```json
{
  "pdf_id": "665f1a2b3c4d5e6f7a8b9c0d",
  "filename": "informe.pdf",
  "content_base64": "JVBERi0xLjQKJcOkw7zDtsO4CjIgMCBvYmoKPDwvTGVuZ3RoIDMgMCBSPj4K...",
  "checksum": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"
}
```

### Ejemplo — resultado publicado por el extractor

```json
{
  "pdf_id": "665f1a2b3c4d5e6f7a8b9c0d",
  "extracted_text": "Contenido de texto del PDF...",
  "status": "done"
}
```

Nota: el resultado de la extracción (texto plano) no necesita base64 — solo el contenido binario original (el PDF en sí) lo requiere. Base64 se aplica únicamente donde hay bytes no-texto de por medio.

## Consecuencias

**Positivas:**
- Cumple la restricción de RAM: el binario nunca toca disco, viaja embebido en el mensaje.
- JSON + base64 es soportado de forma nativa (o con una línea de código) en prácticamente cualquier lenguaje — no requiere herramientas de serialización adicionales (Protobuf, Avro, etc.).
- El contrato de nombres (`snake_case` fijo en el wire) es independiente del lenguaje, evita ambigüedad entre servicios.

**Negativas / a tener en cuenta:**
- Base64 incrementa el tamaño del payload en aproximadamente un 33% respecto al binario original — no es un problema al tamaño de PDF que maneja este proyecto (`MAX_FILE_SIZE_MB` ya limitado), pero no es gratis.
- Cada servicio necesita decodificar explícitamente el campo `content_base64` antes de operar sobre los bytes reales — es un paso manual que hay que recordar en cada lenguaje.

## Alternativas descartadas

- **Formato de serialización binario (Protobuf/Avro)**: evita el overhead de base64 y es más eficiente, pero exige generar código desde un esquema compartido y herramientas específicas por lenguaje — complejidad de más para el tamaño de este proyecto, y ninguno de los servicios necesita ese nivel de performance.
- **Pasar solo una referencia y guardar el binario en disco/objeto compartido (GridFS, volumen)**: descartado directamente por la restricción de RAM del profesor — cualquier variante que persista el binario en disco compartido, aunque sea temporalmente, viola la regla.
