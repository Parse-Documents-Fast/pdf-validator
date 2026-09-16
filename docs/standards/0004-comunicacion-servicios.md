# ADR-0004: Comunicación entre servicios — núcleo/transporte y cola vs. HTTP por rol

**Estado:** Aceptado

## Contexto

Nada de esto está publicado todavía, así que se define de una sola vez, sin parches posteriores. Además de separar lógica de negocio del transporte, hace falta un criterio explícito de **cuándo** un servicio se comunica por HTTP síncrono y cuándo por cola asíncrona — no un caso por caso ad-hoc, sino una regla que cualquier servicio nuevo pueda seguir sin tener que discutirlo de nuevo.

## Decisión

### 1. Separación núcleo / transporte
Todo servicio implementa su lógica de negocio como una función pura, sin conocimiento de HTTP ni de colas. El adaptador (handler HTTP o consumer de stream) es una capa delgada que solo traduce entrada/salida.

```go
func ExtractStructure(content []byte) (Documento, error) { /* núcleo */ }
func HandleExtract(w http.ResponseWriter, r *http.Request) { /* adaptador HTTP */ }
func ConsumeExtractionQueue(msg RedisMessage) { /* adaptador de cola, llama al mismo núcleo */ }
```

### 2. Criterio para elegir transporte
**¿El resultado de este servicio gatilla una decisión dentro del mismo request de quien lo llama? → HTTP síncrono.**
**¿Es un resultado terminal que nadie necesita esperar en el momento? → cola.**

| Servicio | Transporte | Por qué |
|---|---|---|
| `pdf-validator` | HTTP síncrono | Su resultado (PDF o Markdown) determina a qué servicio llama `pdf-main` después, en el mismo request. Ponerlo en cola obligaría a diferir esa decisión de ruteo y cambiaría el contrato de error inmediato en validación. |
| `pdf-extractor` | Cola (Redis Streams) | Resultado terminal — el cliente ya recibió `pending`, nadie lo espera en el momento. |
| `pdf-converter` — ingesta (Markdown → HTML) | Cola (Redis Streams) | Mismo caso que `pdf-extractor`: resultado terminal del flujo de subida. |
| `pdf-converter` — descarga (HTML → formato pedido) | HTTP síncrono | El cliente está esperando activamente un archivo en esa misma conexión — no hay "pending" posible en una descarga. |
| `pdf-transformator` | HTTP síncrono | Invocado internamente por `pdf-extractor` dentro de su propio procesamiento async — nunca bloquea a `pdf-main` ni al cliente, independientemente de su latencia propia. |
| `pdf-persistance` | HTTP síncrono | Único punto de contacto: siempre `pdf-main`, nunca otro servicio directamente. |

### 3. Mecanismo de cola (aplica a extracción y a la ingesta de conversión)
- **Redis Streams** con consumer groups (`XREADGROUP`/`XACK`), no listas simples — permite reclamar un job si el worker muere antes de confirmarlo.
- **Correlación** por `pdf_id`, ya único desde que se crea el registro en Mongo — sin IDs adicionales.
- Streams: `queue:extraction` / `queue:extraction-results`, `queue:conversion` / `queue:conversion-results`.
- `pdf-main` corre su servidor HTTP de siempre, más una goroutine por cada stream de resultados que consume, y llama a `pdf-persistance` al recibir cada uno — sigue siendo el único que le habla a persistencia.

## Consecuencias

**Positivas:**
- El criterio es repetible: un servicio nuevo se clasifica preguntando "¿bloquea una decisión en el mismo request?", no por intuición caso a caso.
- `pdf-converter` queda consistente internamente (ambas responsabilidades bien justificadas, no las dos por default a lo mismo).

**Negativas / a tener en cuenta:**
- `pdf-main` corre múltiples procesos en paralelo (HTTP + N consumers) — más superficie de manejo de errores y reconexión a Redis que un servicio HTTP puro.
- El equipo necesita entender consumer groups de Redis Streams, no solo Redis como cache.

## Alternativas descartadas

- **Todos los servicios por cola, sin excepción**: descartado porque `pdf-validator` gatilla una decisión de ruteo que `pdf-main` necesita en el mismo request — forzarlo a cola cambia el contrato de error inmediato en validación, no es una decisión solo de transporte.
- **Todos los servicios por HTTP, sin excepción**: descartado porque no resuelve el riesgo de timeout ya identificado en extracción y, por el mismo motivo, en la ingesta de conversión.
