# Recopilación editorial de Curio25

El módulo `curio25.research` toma los 25 candidatos pendientes, consulta las páginas oficiales (NOAA, NASA, NPS, LOC), conserva texto con SHA256 y guarda búsquedas de hasta tres imágenes de Wikimedia Commons por curiosidad. NO marca ninguna afirmación como verificada ni ninguna foto como aprobada.

```bash
python -m curio25.research --episode 2026-11-17 --out build/research-2026-11-17
```

Resultados: `source_report.json`, `image_suggestions.json`, carpeta `snapshots/`. El job automático los ofrece como artefacto y crea una PR de revisión si dispone de permisos. Cada imagen necesita inspección de licencia, autor y pertinencia antes de descargarla. Después se deben incorporar datos e imágenes al catálogo validado, pasar tests y renderizar. No modifica YouTube.

Referencias corregidas: primer vuelo Wright (LOC Today in History - December 17) y litros Old Faithful (NPS Old Faithful Geyser).
