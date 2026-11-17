# Curio25 — instrucciones para ChatGPT y otros agentes de desarrollo

Este repositorio es independiente de UMBRAL. Trabajar solo aquí; no modificar `fedry23/umbral-automation` ni sus workflows.

## Cambios habituales mediante la integración GitHub

- Configuración: `config.json` (hora local Europe/Madrid, canal y barreras de publicación).
- Contenido: `data/facts.json`, fuentes en `data/source_audit.json` y `data/snapshots/`.
- Candidatos pendientes: `data/candidates/*.json`; **leerlos antes de investigar nuevos temas**, no duplicar sus afirmaciones ni promoverlos sin fuentes/medios completos. Los candidatos `pending` no deben añadirse a `data/facts.json` ni considerarse verificados.
- Fotografías: `data/media/assets.json` y registros de licencia adyacentes.
- Estética y zonas seguras: `curio25/layout.py`, `art.py`, `render.py`.
- Componentes del motor: `curio25/video_io.py` (FFmpeg/validación), `curio25/captions.py` (SRT/ASS), `curio25/episode_meta.py` (tema/título); `curio25/render.py` coordina el render y mantiene imports antiguos.
- Operación: `.github/workflows/`, `docs/` y README.

Antes de editar, leer README y los archivos afectados con la integración GitHub. Crear una rama y un pull request con el cambio concreto cuando sea posible. Para cambios multarchivo, publicar un único commit coherente; no dejar una referencia a una foto/modelo ausente. No asumir que una respuesta de la integración equivale a tests ejecutados: comprobar el workflow de tests del commit y su resultado.

## Identidad narrativa y musical de Curio25

- **No escribir como enciclopedia**: empieza cada curiosidad con una sorpresa, contraste, pregunta o comparación, explica el hecho en castellano de España y termina con un remate breve cuando encaje; evitar muletillas repetidas, chistes forzados y cinco temas similares seguidos.
- **Precisión antes que espectáculo**: contrastar el dato con fuente fiable, comprobar cifras, unidades, fechas, ámbito de las estimaciones y evitar atribuir a NASA o a un inventor exclusivo lo que fue una contribución. Si hay discrepancia, usar atribución y cautela o sustituir el dato. No elevar un candidato `pending` a `verified` con una coincidencia textual.
- Guion para voz masculina española sintética: normalmente 23–32 palabras por dato, evitando abreviaturas difíciles, pronunciaciones extranjeras no tratadas y enumeraciones frías. Usar `curio25.voice_style.for_speech` solo para el audio; el texto visible siempre conserva ortografía correcta. Escuchar el MP4 completo antes de aprobar.
- Alternar animales, ciencia, historia, tecnología, naturaleza y otros temas; no duplicar en el mismo vídeo el mismo descubrimiento con otra fecha. Guardar vínculo imagen–dato mediante ID.
- Música de marca: instrumental original ligero y juguetón; nada de música, fragmentos o melodías de XpressTV. Aplicar ducking para priorizar la voz. La intro/outro, el reloj y las zonas de subtítulos no deben alterarse ni durar más de cinco minutos en conjunto.
- Referencia de implementación: `docs/VOICE_MUSIC_EDITORIAL_V2.md`. Los renders de candidatos son **previsualizaciones no publicables**.

## Continuidad anual y cola de publicación

- El objetivo son **365 episodios al año** (366 en un año natural bisiesto) y **25 hechos únicos por episodio**, no 365 reutilizaciones del piloto.
- Mantener una **reserva mínima de 30 episodios revisados** (750 hechos con 750 imágenes licenciadas), una reserva deseable de 60 y una alerta crítica por debajo de 7.
- El módulo `curio25.queue` selecciona siempre lotes FIFO de 25 hechos del mismo `episode_topic` y título. No usar `[:25]` global cuando se mezclen temáticas.
- El workflow `annual-coverage.yml` evalúa diariamente la reserva, conserva informes y abre/actualiza una única incidencia hasta que se recupere la cola. Una incidencia abierta no significa que se hayan aprobado fuentes o fotos.
- El segundo cron de `daily.yml` es una oportunidad de recuperación: el mismo identificador de episodio y el historial evitan duplicar la reserva. Los cron de GitHub pueden retrasarse o perderse: no garantizan puntualidad.
- A medio plazo, con OAuth y consentimiento de publicación explícitos, preparar y programar semanas de MP4s privados para que YouTube publique a la hora deseada. **No activar automáticamente** esa fase.
- Una tarea editorial que solo aporta 25 datos al día no puede crear reserva mientras se consumen 25: hace falta producir y revisar más de un día de datos por cada día de emisión durante la fase de arranque.

## Invariantes

- Publicación YouTube desactivada hasta aprobación explícita del usuario y OAuth del canal. No cambiar `publication_enabled`, `approved_episode_sha256` ni añadir pasos de publicación al workflow por una petición genérica de mejora estética o contenido.
- Exactamente 25 datos revisados por episodio; 300 segundos ±5, 1920×1080. No acelerar voz para encajar un guion largo.
- Mantener íntegro `data/history.json`; nunca borrarlo para superar el control de duplicados. Las revisiones visuales de un episodio sin subir usan `revise`, no vuelven a reservar los datos como episodio nuevo.
- Subtítulos en banda exclusiva inferior, máximo2líneas, sin solapar contenido. Medir cajas y ejecutar tests de layout.
- No introducir secretos, tokens, credenciales ni modelos de pago. No instalar servicios de facturación.
- No marcar fuentes o licencias como verificadas sin consultar evidencias. No copiar párrafos. Las fotos deben tener autor, licencia comercial explícita, URL y hash.

## Verificar y comunicar

Ejecutar `python -m pytest -q` tras cambios. Si afecta composición, generar el episodio (`python -m curio25 revise --episode pilot-001 --out build/pilot-002`) y ejecutar validación completa; revisar varios fotogramas, también con subtítulos largos. Adjuntar el resultado y los límites de lo que se pudo probar. Una aprobación de un MP4 antiguo no aprueba un render nuevo.

GitHub necesita acceso de la integración a este repositorio nuevo. Esa autorización se gestiona en GitHub/ChatGPT, no mediante tokens dentro del código. Configurar el workflow de Actions del repositorio para la validación en nube. No garantizar monetización ni coste gratuito universal de Actions.
