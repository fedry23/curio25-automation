# Previsualización NO PUBLICAR del segundo episodio

El primer episodio completo ha demostrado el funcionamiento del montaje.
Para revisar el siguiente lote de 25 datos se usa **sólo** la cuarentena:

- `data/candidates/2026-11-17.json`: guion pendiente de aprobación.
- `data/candidates/research-2026-11-17/`: 16 capturas institucionales y SHA256.
- `data/candidates/media-2026-11-17/`: 25 fotos con metadatos y SHA256 pendientes de revisión.

`python -m curio25.preview --preflight-only` verifica la coherencia. El
render `python -m curio25.preview` NO reserva datos, NO modifica
`data/facts.json`, `data/history.json`, `data/media/assets.json` ni
`config.json`, y no incluye acciones de subida. Tiene una marca visible
**BORRADOR · NO PUBLICAR** en las 25 escenas y la miniatura.

El workflow `.github/workflows/preview.yml` deja el vídeo como artefacto
temporal de GitHub Actions durante siete días. No es una producción aprobada.
La descarga de un medio con licencia declarada NO garantiza derechos de uso;
hay que inspeccionar los 25 fotogramas/medios y sus atribuciones, comprobar
los hechos con la fuente original y retocar títulos/ritmo/voz si procede.
El borrador conserva todos los créditos aunque la descripción exceda el
límite de YouTube; no debe subirse. La publicación oficial sigue bloqueada.

Para el episodio final habrá que convertir las evidencias y licencias
efectivamente revisadas a los catálogos de producción, mantener un texto de
atribuciones compatible con las normas de Commons y el límite de 5000
caracteres de YouTube, revisar el vídeo final y permitir OAuth sólo para el
canal ya existente.
