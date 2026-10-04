# PR: Configuración de evaluación y benchmark para el TP (Issue #19)

## Descripción del Problema
Para las pruebas de carga y estrés del Trabajo Práctico (evaluadas mediante k6 y Vegeta), se requería un entorno de ejecución estricto y equitativo para todos los grupos. Sin embargo, el archivo original `docker-compose.yml` está optimizado para desarrollo local (sin límites de hardware, sin escalar y enfocado en iteración rápida).

Para asegurar la imparcialidad del benchmark, el entorno de evaluación debe cumplir con las siguientes restricciones según las pautas establecidas por la cátedra:
1. **Límites de hardware explícitos** (por ejemplo, máximo 1.0 CPU y 512 MB a 1 GB de RAM por réplica).
2. **Escalabilidad horizontal máxima** de hasta 5 réplicas/instancias.
3. Uso de un **balanceador de carga inverso** para distribuir el tráfico equitativamente entre las réplicas.

## Solución Propuesta (Cambios en esta PR)
Se creó un archivo secundario `docker-compose.tp.yml` derivado de la arquitectura principal con las siguientes incorporaciones:
- **Balanceador Inverso Traefik:** Se configuró un servicio Traefik expuesto en el puerto 80 para orquestar y distribuir uniformemente el tráfico entrante a los contenedores de procesamiento.
- **Réplicas y Escalabilidad:** Se configuró el servicio `pdf-validator` con `deploy.replicas: 5` para instanciar exactamente 5 nodos de procesamiento.
- **Límites de Recursos:** Se asignaron restricciones de hardware específicas (`cpus: '1.0'`, `memory: 512M`) a través del bloque `deploy.resources.limits` para las instancias de `pdf-validator`.
- **Integración con Traefik:** Se incluyeron las etiquetas correspondientes (`labels`) en `pdf-validator` para exponer la ruta obligatoria `/extract` en el puerto 8000 hacia el reverse proxy.
- **Variables de Entorno:** Se estableció `ENV=production` y `MAX_FILE_SIZE_MB=10`.

## Pruebas
- Se validó el archivo `docker-compose.tp.yml` verificando su correcta sintaxis con `docker compose config`.
- (Opcional) Ejecutar `docker compose -f docker-compose.tp.yml up --build` localmente asegurará la creación del balanceador y las 5 réplicas de acuerdo a los límites establecidos.
