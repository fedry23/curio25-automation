# Contrato editorial para la preparación diaria de Curio25

Este documento es la referencia de producción para el agente que investiga y
prepara los siguientes 25 datos curiosos. El programa **nunca inventa
referencias ni autoriza fuentes automáticamente**.

## Flujo de producción

1. Leer `data/history.json` y `data/facts.json` para evitar repetir ideas,
   afirmaciones, temas, identificadores y fotografías. Trabajar en rama nueva.
2. Investigar 25 hechos diferentes, preferentemente en fuentes primarias o
   instituciones fiables; guardar texto consultado realmente en
   `data/snapshots/` y registrar URL, hash SHA256 y fecha en
   `data/source_audit.json`. Redactar texto ORIGINAL, en español de España,
   preferiblemente entre 25 y 40 palabras por curiosidad.
3. Para cada dato, establecer `id` único, `title`, `claim`,
   `narration`, `source_url`, `evidence_query`, `evidence_excerpt`,
   `source_snapshot_sha256`, `body`, `graphic`, `episode_topic`,
   `review_status` y campos de trazabilidad de revisión. Marcar
   `verified` **únicamente tras haber leído y comprobado la fuente**.
   Si hay incertidumbre, dejar candidatos en `data/candidates/` y no añadirlos
   al catálogo de producción.
4. Los 25 hechos deben compartir `episode_topic`, que sirve de título del
   episodio; para mezclar ciencia, historia, animales, tecnología y naturaleza
   usar `curiosidades del mundo`. Opcionalmente definir `episode_title`
   coherente en los 25 datos. Nunca escribir título de sistema solar para
   un lote de otros temas.
5. Cada dato nuevo requiere una imagen real pertinente con ficha aprobada
   vinculada por `fact_id` en `data/media/assets.json`. Guardar el archivo
   en `data/media/` y verificar autor, URL de origen, licencia que permita
   uso comercial, `sha256` y `review_status: approved`.
   Se admiten fotos de Wikimedia Commons con metadatos revisados y obras
   claramente autorizadas; **no asumir que una búsqueda concede derechos**.
6. Ejecutar `python -m curio25.editorial` y `pytest -q`.
   El chequeo editorial comprueba integridad del catálogo, existencia de
   evidencias, duplicados y derechos registrados; **no certifica la verdad
   material de cada frase ni resuelve todas las restricciones legales**.
7. Abrir PR y revisar que las 25 curiosidades están listas antes de fusionar.
   El programa diario solo utiliza datos ya revisados; si faltan, se omite el
   render, nunca reutiliza el piloto.

## Lo que no debe hacer el agente

- Nunca publicar automáticamente sin la autorización OAuth del propietario,
  aprobación del canal y pruebas de subida; `publication_enabled` permanece
  `false`.
- Nunca modificar UMBRAL o editar nombre/foto/banner/vídeos del canal YouTube.
- Nunca inventar medios, fuentes, hashes o resultados de pruebas.
- Nunca considerar que el recuento de tests garantiza monetización.
- Nunca copiar grandes fragmentos de las fuentes a los guiones.
- Nunca reutilizar una foto de forma engañosa para representar un hecho distinto.

El objetivo es una base editorial rigurosa y entretenida, no producir volumen
a costa de la exactitud.
