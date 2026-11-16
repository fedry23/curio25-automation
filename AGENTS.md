# Curio25 — instrucciones para ChatGPT y otros agentes de desarrollo

Este repositorio es independiente de UMBRAL. Trabajar solo aquí; no modificar `fedry23/umbral-automation` ni sus workflows.

## Cambios habituales mediante la integración GitHub

- Configuración: `config.json` (hora local Europe/Madrid, canal y barreras de publicación).
- Contenido: `data/facts.json`, fuentes en `data/source_audit.json` y `data/snapshots/`.
- Fotografías: `data/media/assets.json` y registros de licencia adyacentes.
- Estética y zonas seguras: `curio25/layout.py`, `art.py`, `render.py`.
- Operación: `.github/workflows/`, `docs/` y README.

Antes de editar, leer README y los archivos afectados con la integración GitHub. Crear una rama y un pull request con el cambio concreto cuando sea posible. Para cambios multarchivo, publicar un único commit coherente; no dejar una referencia a una foto/modelo ausente. No asumir que una respuesta de la integración equivale a tests ejecutados: comprobar el workflow de tests del commit y su resultado.

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
