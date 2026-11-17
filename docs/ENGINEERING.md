# Arquitectura técnica de Curio25 (17/11/2026)

## Módulos y responsabilidades

| Módulo | Propósito |
| --- | --- |
| `curio25/render.py` | Coordina voz, imagen, escenas, intro/outro, reloj y mezcla final |
| `curio25/video_io.py` | Ejecuta FFmpeg/ffprobe, comprueba resolución, audio y decodificación |
| `curio25/captions.py` | Genera marcas de tiempo, subtítulos SRT y ASS |
| `curio25/episode_meta.py` | Valida el tema y crea el título de cada episodio |
| `curio25/state.py` | Reserva y restaura el historial (JSON atómico + SQLite) |
| `curio25/preview.py` | Borrador privado de los 25 datos; **nunca marca revisión ni publica** |
| `curio25/editorial.py` | Audita los registros de fuentes y licencias antes de producir |
| `curio25/soundtrack.py` / `voice_style.py` | Música propia, mezcla con ducking y pronunciación |

Los imports heredados `from curio25.render import stamp, write_ass, validate, episode_identity` siguen disponibles. No es necesario actualizar scripts antiguos.

## CI y coste de ejecución

- El workflow **Tests** se ejecuta al abrir/actualizar una PR y al integrar en `main`, no dos veces por el mismo push de rama.
- Las ejecuciones de una PR anteriores se cancelan cuando llega una versión nueva.
- FFmpeg y fuentes se instalan únicamente si el runner no los tiene.
- Se cachean paquetes Python según `requirements.lock`; en renders se reutiliza el modelo Piper con un identificador asociado al SHA256 esperado. `scripts/download_voice.py` **sigue verificando el hash** después de restaurarlo.
- El workflow de **previsualización** audita material y ejecuta pruebas focalizadas; el workflow Tests independiente ejecuta la batería completa.
- Un cambio en el lote candidato o sus fotos también actualiza la previsualización, sin tocar `data/history.json` ni YouTube.
- El workflow diario verifica primero que existan 25 hechos **nuevos y revisados**; si faltan, no descarga modelos ni renderiza.

## Notas de seguridad y límites

- **Publicación desactivada**: estos cambios no alteran `config.json`, `data/history.json` ni la lógica de OAuth/subida. UMBRAL sigue siendo otro proyecto.
- La serialización atómica del historial evita archivos JSON truncados ante fallos durante la escritura. No sustituye la necesidad de coordinar dos escritores externos simultáneos ni de supervisar los estados `uploading`.
- Mantener el guion original, el MP4 de cinco minutos, música divertida, intro/outro y reloj.
- La revisión editorial y de licencias del segundo episodio sigue pendiente; un test técnico no aprueba un vídeo para publicación.
