# Curio25 Automation

MVP independiente para un canal educativo de curiosidades en castellano de España. Python + FFmpeg + Piper, sin APIs de generación de pago. **Publicación desactivada.** No depende de UMBRAL ni modifica otro repositorio.

## Qué entrega

Un piloto de **25 datos del sistema solar**, guion original, voz masculina española `davefx`, fotografías reales de dominio público y diagramas específicos originales, movimientos de cámara dentro de la fotografía, transiciones claras/oscuras, música ambiental y pequeños acentos sonoros sintetizados. Salida horizontal H.264/AAC a 1920×1080, 25 fps, 300 segundos (validación ±5 s). Subtítulos derivados de las duraciones reales de cada oración, incrustados y SRT. Incluye miniatura, título, descripción, capítulos, créditos, fuentes, manifiesto de recursos y validación técnica.

Es un **MVP de producción y revisión**, no una fábrica de episodios infinitos. Hay 25 datos verificados: tras el piloto, el sistema se detiene por catálogo agotado. Para publicar a diario hacen falta al menos 175 datos nuevos revisados por semana. La investigación y la calidad editorial no se pueden sustituir por comprobar que una URL responde. El piloto actualizado integra once fotografías de dominio público de NASA y sus colaboradores, vinculadas a las25 escenas; registra autor, licencia, fuente y SHA256. Las fotografías usan movimiento dentro de una caja propia. No se generan nuevos guiones mediante un modelo en la nube: el guion editorial viene del catálogo revisado.

## Instalación y ejecución

Requiere Linux, Python 3.12, FFmpeg con libass/libx264 y fuentes DejaVu. En Ubuntu: `sudo apt-get install ffmpeg fonts-dejavu-core`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
python scripts/download_voice.py
pytest -q
python -m curio25 revise --episode pilot-001 --out build/pilot-002
python -m curio25 validate --out build/pilot-002
```

El piloto actualizado se genera en `build/pilot-002/episode.mp4`. La entrega contiene un MP4 completo, también conservado en `examples/pilot-002/episode.mp4` en GitHub. Su historial está guardado. Si el vídeo se encuentra en estado `rendered`, no se vuelve a generar bajo ese identificador. El comando `revise` mantiene los mismos25 datos y solo admite episodios sin subir. Para experimentar sin afectar el historial, copia el proyecto a otra carpeta y elimina **solo en esa copia** `data/history.json` y `data/history.sqlite*`. No borres el historial de un canal en producción. Un render fallido queda `reserved`; repetir el mismo comando reanuda la reserva y vuelve a renderizar. No aumenta la velocidad del TTS para encajar: rechaza un guion demasiado largo o corto y exige editarlo.

`config.json` contiene el horario (18:00 Europe/Madrid por defecto). El render usa las dimensiones y fps de producción fijados en código; los campos width/height/fps documentan ese formato, no permiten otros formatos en este MVP. El objetivo del MVP es siempre 300 segundos.

## Fuentes y catálogo

`data/facts.json` es la fuente editorial versionada. Cada registro contiene afirmación, narración original, URL, fragmento de evidencia, hash de la captura, revisión y especificación del gráfico. `data/source_audit.json` registra recuperación y SHA256 de cada fuente; `data/snapshots/` conserva texto para auditoría. Las páginas de NASA se consultaron durante la implementación, el 16 de noviembre de 2026. Se corrigieron una URL de Plutón inexistente y consultas de evidencia ambiguas. El dato lunar se cambió a distancia media porque la página consultada no respaldaba con precisión el valor inicial de alejamiento.

Para añadir datos: documentar afirmación y condiciones; leer la fuente primaria; redactar una explicación propia de unas 30–40 palabras; aportar un gráfico o recurso pertinente; revisar licencia y texto; registrar evidencia; marcar `verified` **solo tras esa revisión**. No copiar párrafos. Si el dato es controvertido o cambia con el tiempo, añadir una segunda fuente y fecha contextual. Evitar repetir la misma idea con otras palabras: el hash de texto no detecta duplicados semánticos.

```bash
# Refresca capturas y muestra contexto; NO aprueba datos ni actualiza su revisión.
python -m curio25.sources
```

Al refrescar una fuente, sus hashes cambian: hay que revisar y actualizar los registros afectados antes de renderizar. El historial conserva identificadores y hashes de afirmaciones para bloquear reutilización. SQLite realiza la reserva en una transacción y `data/history.json` permite persistirla entre runners. El estado `uploading` se conserva para impedir cargas duplicadas tras una interrupción.

## Recursos y licencias

El piloto usa fotografías científicas reales de dominio público (mosaicos, radar y colores procesados se identifican en pantalla). Los diagramas son esquemas originales, señalados sin escala; las barras numéricas sí comparan los valores indicados. Las barras de temperaturas Celsius no representan proporciones físicas de calor. La música y los efectos proceden de una composición determinista en `render.py`, sin muestras ni canciones ajenas. Créditos individuales y hashes se escriben en `assets.json` y `data/media/assets.json`.

Para importar una imagen de Commons explícita:

```python
from curio25.sources import commons_asset
record = commons_asset('File:Nombre exacto del archivo.jpg', 'data/media')
```

La función consulta metadatos del archivo, exige autor/licencia comercial de la lista permitida, descarga y conserva un registro. Una búsqueda no acredita derechos. Revisar además la página original y posibles derechos de imagen, marcas y restricciones ajenas al copyright. El render enlaza automáticamente cada dato con la fotografía aprobada de su cuerpo celeste mediante `curio25/media.py`. Para nuevos temas, ampliar el inventario explícito `data/media/assets.json`, revisar derechos y actualizar su asociación; un resultado de búsqueda no se incorpora sin revisar. Los créditos completos se conservan en el manifiesto y la descripción. CC BY-SA puede exigir compartir la adaptación bajo la misma licencia. No se permiten NC, ND, licencias ambiguas ni archivos sin autor. Ante cuotas, bloqueo o incertidumbre, usar gráficos propios o detenerse; nunca quitar controles de licencia.

Voz: ficha en `models/MODEL_CARD`, fuente [Piper voices](https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_ES/davefx/medium), dataset CC0, base CC0 según la ficha. Modelo y configuración se comprueban con hashes aprobados. Piper actual se distribuye bajo GPL-3.0; ONNX Runtime y demás dependencias conservan sus licencias. No se redistribuyen los binarios en Git. Consultar `docs/LICENSES.md`.

## GitHub y ejecución diaria

Repositorio: [fedry23/curio25-automation](https://github.com/fedry23/curio25-automation). Es independiente de UMBRAL. La integración no tenía permiso para crearlo; el propietario lo creó y autorizó acceso antes de la subida.

Para editarlo desde ChatGPT, conceder a la integración GitHub acceso a este repositorio y seguir [AGENTS.md](AGENTS.md) y [la guía de edición](docs/EDITING_WITH_CHATGPT.md). Configuración y catálogo son archivos versionados; los cambios pueden revisarse en una rama/PR con tests de Actions. No hace falta incluir credenciales en el proyecto.

El workflow de render se programa a las 05:15 UTC y admite ejecución manual. La hora de render es independiente de la publicación; UTC evita duplicar un cron al cambiar el horario de verano. GitHub puede retrasar o saltarse ejecuciones programadas; no es un servicio con SLA. En repositorios públicos la programación puede desactivarse por inactividad. El estado se guarda en un commit y los resultados como artefactos durante 3 días. Se serializan ejecuciones; se conservan logs incluso si falla. Configura las notificaciones por correo de Actions en GitHub para recibir alertas; `::error::` marca el fallo en la interfaz, no envía correos por sí solo. El workflow de tests no necesita credenciales ni permisos de escritura.

El workflow diario **solo renderiza**. En ejecución manual permite elegir `review_pilot` para regenerar el piloto existente sin reservar nuevos datos; `daily` requiere un lote nuevo. No contiene un paso de subida, incluso aunque cambies la configuración. Con el catálogo inicial agotado fallará de forma explícita. Para producción conviene separar reserva, cola editorial aprobada y publicación, y conservar los MP4 en almacenamiento duradero; los artefactos de Actions caducan. Los commits del historial no desencadenan otro render (este workflow solo escucha schedule/manual).

## Conectar YouTube y aprobar un episodio (pendiente)

1. Ver el vídeo entero, escuchar la voz y revisar fuentes, derechos, miniatura y subtítulos.
2. Crear un proyecto propio en Google Cloud y activar **YouTube Data API v3**. Configurar la pantalla de consentimiento OAuth y un cliente de **aplicación de escritorio**. Descargar su JSON fuera del repositorio. Con scopes restringidos puede ser necesaria verificación; los refresh tokens de aplicaciones externas en modo de pruebas pueden expirar a los 7 días. Google también puede restringir a privado las cargas de proyectos API no auditados.
3. En tu ordenador con navegador: `export YOUTUBE_CLIENT_FILE=/ruta/cliente.json`, después `python -m curio25 auth`. El flujo oficial de loopback abre consentimiento, sin pedir contraseñas al programa. Solicita `youtube.upload` y `youtube.force-ssl`; este último permite gestionar la pista de subtítulos con `captions.insert` y verificar el canal autorizado. Guarda `token.json` como secreto. Nunca subirlo a Git.
4. Configurar `channel_id` con el identificador real del canal, revisar `contains_synthetic_media` de `metadata.json` y poner `approved_episode_sha256` igual al SHA256 del MP4 aprobado. Después activar `publication_enabled`. Cada nuevo MP4 necesita aprobación propia en este MVP.
5. Para probar la integración autorizada: `YOUTUBE_TOKEN_FILE=/ruta/token.json python -m curio25 upload --episode pilot-001 --out build/pilot-002`. **Este comando programa publicación real** a la siguiente hora configurada, como mínimo una hora después. No ejecutarlo antes de aprobar. El MP4 se carga inicialmente privado con `publishAt` UTC; la hora local se calcula con `zoneinfo`, incluyendo horario de verano. Se rechazan horas locales inexistentes.
6. Para ejecutarlo en nube, guardar el JSON OAuth autorizado en el secreto `YOUTUBE_TOKEN_JSON`, y añadir deliberadamente el paso de subida al workflow después de establecer un mecanismo de revisión por episodio. No se añade aquí para impedir publicación accidental. No poner credenciales en YAML ni archivos versionados.

La API oficial usa carga reanudable por bloques de 8 MiB, reintentos con espera exponencial para 429 y errores transitorios. Los errores de permisos/cuota no se convierten en bucles infinitos. Se conserva la URI de sesión en SQLite (dato sensible, ignorado en Git), pero tras una interrupción del proceso **no se inicia otra carga automáticamente**. Revisar en YouTube Studio y conciliar ID/estado antes de desbloquear; el MVP prioriza evitar duplicados. La miniatura y pista SRT se suben después de obtener el ID. Si fallan, el vídeo ya puede estar programado: revisar el ID guardado, corregir esos elementos o cancelar la programación en Studio.

## Costes, calidad y monetización

No hay suscripción necesaria ni consumo de un modelo de pago. El render no usa APIs TTS con cuotas: funciona localmente en el runner una vez descargada la voz. El catálogo y los gráficos propios funcionan sin red. La primera descarga requiere Hugging Face y sus condiciones; si no está disponible, se detiene hasta proporcionar el modelo con el mismo hash. Commons aplica límites; se respetan 429 y `Retry-After`. YouTube impone cuotas y condiciones del proyecto: consultar las vigentes en la consola y documentación; no asumir capacidad ilimitada.

GitHub Actions en repositorios privados tiene minutos y almacenamiento incluidos limitados según plan. No es posible prometer coste cero universal ni ejecución diaria perpetua gratis. Este proyecto no contrata servicios, activa facturación ni compra recursos. Mantener baja la retención, revisar uso y detener programación antes de agotar la cuota; un runner propio evita cobro pero necesitaría una máquina encendida. La alternativa pública tiene otras implicaciones de exposición del código y catálogo.

La originalidad depende de explicaciones, montaje y diseño editorial propios. No basta cambiar voz y colores para monetizar una plantilla repetida. El piloto es un punto de partida: antes de escalar, ampliar la variedad narrativa y los recursos de cada tema, y revisar exactitud, pronunciación y accesibilidad. YouTube evalúa el canal completo y puede rechazar contenido repetitivo o producido en masa. **No se garantiza monetización.**

Se informa de la voz sintética en la descripción. La marca API de contenido sintético se deja en `false` para este piloto de diagramas esquemáticos y voz genérica, sin suplantación ni escenas realistas falseadas. Eso no sustituye la revisión de las reglas vigentes: si se usa una voz clonada o alteraciones realistas sujetas a identificación, cambiar el campo antes de subir. El indicador `selfDeclaredMadeForKids=false` es una decisión editorial inicial para audiencia general, no significa que el vídeo tenga contenido adulto; revisar si cambia la audiencia objetivo.

Políticas y documentación oficial: [monetización](https://support.google.com/youtube/answer/1311392?hl=es), [contenido alterado o sintético](https://support.google.com/youtube/answer/14328491?hl=es), [vídeos insert](https://developers.google.com/youtube/v3/docs/videos/insert), [carga reanudable](https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol), [OAuth de escritorio](https://developers.google.com/identity/protocols/oauth2/native-app).

## Verificación y límites

`pytest -q` cubre procedencia del catálogo, reservas transaccionales, agotamiento, duplicados por ID/afirmación, persistencia, duración sin acelerar, subtítulos, barreras de publicación, horario Madrid invierno/verano y rechazo de licencias. El render final se comprueba con ffprobe, decodificación completa y volumen máximo. No sustituye escucha humana, medición perceptual de calidad, comprobación científica independiente ni una prueba de OAuth real. Consultar `docs/VALIDATION.md` para los resultados de esta entrega.

## Composición y subtítulos sin solapes

El plano se divide en área visual segura (x64..1856,y48..824) y banda exclusiva de subtítulos (y840..1080). Título, indicador, fotografía, gráficos, fuente y créditos tienen cajas independientes. El movimiento de cámara se aplica únicamente a la fotografía, nunca a títulos ni al plano completo. Las animaciones quedan recortadas dentro de sus cajas.

Cada subtítulo tiene como máximo dos líneas, fuente44px en lienzo ASS explícito1920×1080 y fondo semitransparente. Se divide y mide el texto **antes** de sintetizar: el tiempo de cada cue procede de su WAV real. No se elimina la pista ni se estima sincronía por número de palabras. `layout-report.json` registra las cajas y comprueba límites, solapes y recorridos de animación de las25escenas. Cualquier error detiene el render. Las pruebas incluyen frases largas y textos que no caben; el informe es geométrico y se complementa con inspección visual de fotogramas del MP4.

## Identidad Curio25 Fiesta

El rediseño usa Nunito, gradientes alegres, tarjetas redondeadas, fotografías con cámara suave y colores por categoría. La intro animada dura2,4s y la outro2,6s, ambas dentro de los300s. El reloj continuo tiene una cápsula cartoon y la banda de subtítulos sigue siendo exclusiva, máximo2líneas. La voz entusiasta y la música original con ducking se conservan.

Para generar un **borrador sin consumir historial ni aprobar datos/imágenes**: `python -m curio25.preview --out build/festive-identity`. No usar `revise` para este caso. Véase [el diseño y sus garantías](docs/FESTIVE_IDENTITY.md). El MP4 de demostración y las capturas se conservan en `examples/festive-identity/`; están marcados como no publicables.
