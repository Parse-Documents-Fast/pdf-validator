# plan.md — pdf-validator

## Qué hay que construir
Un servicio chico que recibe bytes crudos de un archivo y responde con una clasificación: PDF válido, Markdown válido, o inválido — sin decidir nada más allá de eso.

## Cómo construirlo, en orden
1. Chequeo de PDF: magic bytes (`%PDF-`) y tamaño máximo — reutilizar tal cual la lógica que ya existe en el monolito (`validate_pdf_bytes`), no reinventarla.
2. Chequeo de Markdown: extensión `.md` y que decodifique como UTF-8 válido. Nada más — no se intenta verificar "buen" Markdown, eso es responsabilidad de quien lo escribió, no de este servicio.
3. Calcular el checksum SHA-256 del contenido (se sigue usando para detectar duplicados, independientemente de si es PDF o Markdown).
4. Responder con la clasificación + checksum, o con un error según ADR-0001 si no pasa ninguna de las dos validaciones.

## Fuera de alcance
Cualquier verificación de contenido más allá de "decodifica" (estructura interna del PDF, sintaxis Markdown real) — no es el trabajo de este servicio.
