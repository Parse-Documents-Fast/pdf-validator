# ADR-0005: Markdown como formato canónico; fusión de pdf-extractor y pdf-transformator

**Estado:** Aceptado

## Contexto

El TP de Test de Carga (cátedra) exige que el servicio de extracción devuelva Markdown directamente. Repensando el diseño con ese dato: HTML se había elegido como formato intermedio por ser suficientemente expresivo (headers, tablas, listas) sin perder estructura — pero Markdown cubre exactamente lo mismo. Mantener HTML como canónico ya no aporta nada; solo agrega una capa de traducción (Markdown→HTML en la ingesta, HTML→Markdown en la descarga) que no tiene beneficio real.

Además, `pdf-extractor` y `pdf-transformator` siempre se llaman en el mismo orden, nadie más consume la salida intermedia entre ambos, y corren en el mismo lenguaje (Go) — separarlos en dos servicios de red no compraba escalado independiente ni ningún otro beneficio real, y sí sumaba un salto de red por request, justo cuando el TP de carga mostró que la latencia bajo concurrencia es una métrica que importa.

## Decisión

**1. Markdown pasa a ser el formato canónico persistido**, en vez de HTML. `pdf-persistance` guarda el contenido como Markdown directamente.

**2. `pdf-extractor` absorbe la responsabilidad de `pdf-transformator`.** `pdf-transformator` deja de existir como repo separado. El servicio fusionado extrae la estructura del PDF y la mapea a Markdown en el mismo proceso (dos funciones núcleo internas, `ExtractStructure()` y `EstructuraAMarkdown()`, sin salto de red entre ellas — sigue el principio de ADR-0004). El transporte hacia `pdf-main` no cambia: sigue siendo consumer de Redis Streams (`queue:extraction` / `queue:extraction-results`, ADR-0004), solo que el contenido del resultado ahora es Markdown en vez de HTML.

**3. La ingesta de un archivo Markdown deja de necesitar procesamiento.** Como el contenido ya llega en el formato canónico, subir un `.md` es: `pdf-main` valida (síncrono, como siempre) y persiste directo (síncrono) — sin ningún paso de conversión de por medio. Deja de aplicar el patrón `pending`/polling para este camino, porque no hay ningún cómputo entre validar y guardar. `queue:conversion` y `queue:conversion-results` (definidos para esta ingesta) se eliminan del diseño — no tienen caso de uso.

**4. `pdf-converter` queda con una sola responsabilidad**: convertir Markdown a PDF, únicamente al momento de la descarga, siempre HTTP síncrono (el cliente espera el archivo en esa misma conexión). Ya no tiene responsabilidad de ingesta ni necesita cola.

## Consecuencias

**Positivas:**
- Menos saltos de red en el camino de extracción — beneficio directo medible en el TP de carga.
- Persistencia más simple: un solo formato, sin necesidad de convertir en la ingesta.
- `pdf-converter` queda con una sola dirección de conversión y una sola responsabilidad — más fácil de razonar y de testear.
- El camino de subida de Markdown se vuelve trivial (validar + persistir, sin async).

**Negativas / a tener en cuenta:**
- `pdf-extractor` pasa a tener dos responsabilidades internas (extraer + mapear a Markdown) en un solo repo — reduce la cantidad de servicios separados del sistema. Si la cátedra evalúa granularidad de descomposición como criterio en sí mismo, vale la pena confirmarlo — el ADR-0004 ya mitiga el riesgo técnico manteniendo las dos funciones núcleo separadas internamente, pero no resuelve una posible objeción de "menos servicios de los esperados".

## Alternativas descartadas

- **Mantener HTML como canónico**: descartado porque no aporta expresividad que Markdown no tenga ya, y agrega conversión en dos direcciones sin beneficio.
- **Mantener `pdf-extractor` y `pdf-transformator` como servicios de red separados**: descartado por el salto de red innecesario — nadie más consume la salida intermedia entre ambos.
