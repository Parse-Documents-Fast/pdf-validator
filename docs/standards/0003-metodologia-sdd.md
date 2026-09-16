# ADR-0003: Metodología SDD (Spec-Driven Development) en cada repo

**Estado:** Aceptado

## Contexto

El sistema se compone de varios repos independientes, potencialmente trabajados por distintas personas del equipo en paralelo, en distintos lenguajes. Sin un flujo de trabajo común, cada repo puede terminar con su propio criterio de "qué significa terminado", dificultando revisar el trabajo de otros o retomar un repo que empezó alguien más.

El profesor pidió aplicar una metodología SDD (Spec-Driven Development) basada en el set de skills de skills.addy.ie, con fases bien definidas, en **cada** repo del sistema.

## Decisión

Todo repo de microservicio sigue el mismo flujo de fases, en este orden:

| Fase | Comando | Qué produce |
|---|---|---|
| **DEFINE** | `/spec` | Documento de alcance: qué hace el servicio, qué NO hace, entradas/salidas, dependencias de otros ADRs (ej. formato de error de ADR-0001, DTOs de ADR-0002) |
| **PLAN** | `/plan` | Desglose en tareas chicas y atómicas a partir del spec |
| **BUILD** | `/build` | Implementación, una rebanada vertical a la vez (no en bloque) |
| **VERIFY** | `/test` | Tests que prueban el comportamiento definido en el spec |
| **REVIEW** | `/review` | Revisión de salud del código antes de mergear |
| **SHIP** | `/ship` | Publicación/merge a la rama principal del repo |

Fases opcionales, a usar cuando aplique: `/webperf` (auditoría de performance, relevante sobre todo para el gateway y servicios con carga alta) y `/code-simplify` (simplificar antes de dar por cerrada una tarea).

El artefacto de la fase `/spec` se persiste en el propio repo como `docs/spec.md`, versionado junto con el código — no es un documento descartable, es la referencia contra la que se valida el `/test` y el `/review` más adelante.

Cualquier decisión transversal (formato de error, DTOs, convenciones de nombres) no se redefine en el `/spec` de cada repo — se referencia el ADR correspondiente de `pdf-docs`.

## Consecuencias

**Positivas:**
- Vocabulario y expectativas compartidas entre repos: cualquiera del equipo que entra a un repo ajeno sabe dónde mirar (`docs/spec.md`) para entender el alcance sin tener que leer todo el código.
- Fuerza la disciplina de "spec antes que código" — reduce el riesgo de construir algo que no coincide con lo que el resto del sistema espera de ese servicio (el mismo tipo de problema que ya vimos con PRs que reescribían lógica fuera del alcance de su propia issue).
- Al estar versionado en el repo, el spec evoluciona junto con el código en vez de quedar desactualizado en un documento externo.

**Negativas / a tener en cuenta:**
- Correr las seis fases completas para un cambio chico (un fix de una línea) es sobrecarga innecesaria — este ciclo aplica al desarrollo de cada microservicio como unidad, no a cada commit o fix puntual dentro de él.
- Requiere que todo el equipo use el mismo skill/herramienta para que las fases sean consistentes entre repos; si alguien lo hace "a mano" con otro criterio, se pierde la comparabilidad entre specs de distintos servicios.

## Alternativas descartadas

- **Desarrollo ad-hoc sin fase de spec formal**: es lo que efectivamente pasó en el monolito original (código y tests después, sin documento de diseño previo) — ya vimos en el análisis de TDD y arquitectura las consecuencias de esa falta de disciplina inicial.
- **Spec centralizado en `pdf-docs` en vez de en cada repo**: descartado porque el alcance de un servicio es información que le pertenece a ese servicio y cambia con su propio ritmo — centralizarlo mezclaría el ciclo de vida rápido de cada repo con el ciclo de vida lento y estable que se busca para `pdf-docs` (ver discusión de ADR vs. catálogo de servicios).
