# Preflight del render diario

Antes de instalar dependencias o descargar la voz, el workflow ejecuta:

    python -m curio25.preflight --mode daily --episode daily-2026-11-17

El comprobador usa solo Python estándar y lee catálogo, fuentes archivadas e
historial; nunca modifica el material editorial ni el historial. Resultados:

- READY: hay 25 datos inéditos verificados y fuentes intactas.
- CATALOG_EXHAUSTED: faltan datos; omite render y marca una anotación en Actions.
- RECONCILIATION_REQUIRED: otra reserva o subida quedó incierta; no duplicar.
- EPISODE_EXISTS: episodio existente; no sobrescribir.
- RESUME: solo se reintenta una reserva del mismo episodio.
- PILOT_REVIEW: la ejecución manual revisa el piloto aún sin subir.
- PILOT_UNAVAILABLE: el piloto ya inició una subida o no existe.

**Esto NO investiga automáticamente datos nuevos.** El catálogo inicial de 25
curiosidades del sistema solar ya está consumido. La publicación sigue
desactivada. Para publicar diariamente de verdad queda ampliar y verificar
fuentes, temas y permisos visuales, ensayar OAuth con el canal existente, y
acordar un servidor de producción y almacenamiento duradero compatible con
las cuotas. Se prohíbe repetir el piloto o activar YouTube para ocultar la falta
de datos.
