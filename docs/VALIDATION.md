# Validación final — Curio25, 16 de noviembre de 2026

- **59 tests superados**: procedencia, fuentes, licencias, reservas/duplicados, revisiones, conciliación de historial, barreras de subida, horario de Madrid, artefactos y layout. Resultado: `logs/tests.txt`.
- Episodio completo: `examples/pilot-002/episode.mp4`, **300.051 segundos**, 1920×1080, 25fps, H.264/AAC.
- Decodificación estricta FFmpeg (`-xerror -err_detect explode`) sin errores; pico -1.1dBFS.
- SHA256: `ce7154846a0cae756b2bc8c3d6500328531b78f5ff3e15c3f3b68bfadce30b84`.
- Exactamente25 datos y25 escenas. Las25 usan fotografía real de su cuerpo celeste y diagramas originales; inventario de11 fotografías de dominio público con autor, fuente y hash.
- 75 cues de subtítulos medidos a partir de sus WAV; máximo 2 líneas. Todas las cajas dentro de la banda exclusiva. Título, número, fotografías, gráficos, fuentes y créditos dentro de zonas seguras; animaciones confinadas.
- Se revisaron seis fotogramas del MP4 final (escenas1,4,9,13,20,25), incluyendo frases largas de doslíneas. No se observaron solapes ni texto cortado. `examples/pilot-002/contact-sheet.jpg` y `visual-review.json` documentan esta revisión.
- Los tests incluyen una rasterización real con FFmpeg/libass: comprueban que los píxeles del subtítulo quedan dentro de la caja reservada. No se depende solo de estimaciones de caracteres.
- 11 fuentes primarias NASA archivadas. La revisión es editorial asistida, no certificación científica independiente. No se ha hecho una escucha humana integral del episodio.
- Publicación desactivada. El rechazo de subida se comprobó antes de OAuth/red (`logs/upload-disabled.txt`). No se subió ni programó contenido en YouTube.

## Cambios y fallos corregidos

Se corrigieron encuadre, textos demasiado grandes de subtítulos, dirección de una flecha y solapamiento de subtítulos con diagramas. El plano ya no se desplaza completo: la cámara se mueve solo en la fotografía. Se añadieron franja inferior exclusiva, medición de tipografía, ASS con lienzo1920×1080 y validación geométrica de25escenas. La revisión independiente también corrigió hashes de narración tras editar un guion reservado, restauración de estados de subida avanzados y validación tolerante de FFmpeg.

La URL inicial de Plutón devolvía404 y se corrigió. Se sustituyó una cifra lunar no respaldada con precisión por su fuente. Un guion inicial era demasiado largo y se recortó sin acelerar el TTS. Los recursos actuales de Commons se descargaron y sus licencias se consultaron realmente; no son archivos ficticios ni recursos pendientes de integrar.

## Pendientes y límites

No probado: OAuth real del canal, cuotas/auditoría de Google y subida/publicación real (desactivada por petición del usuario). Solo hay un lote editorial de25datos; ampliar catálogo antes de pretender episodios inéditos diarios. El modo manual `review_pilot` permite revisar el piloto sin gastar más datos. La recuperación entre procesos de cargas ambiguas exige conciliación manual. Las alertas por correo dependen de configurar notificaciones GitHub. No se garantiza monetización ni gratuidad ilimitada de Actions.
