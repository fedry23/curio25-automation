# Curio25 — plan realista de 365 publicaciones

## Objetivo y cifras

Cada vídeo exige 25 datos inéditos y revisados. Para 365 vídeos se necesitan **9.125 datos originales y 9.125 imágenes pertinentes con derechos comprobados**; para un año natural bisiesto serían 9.150 datos. El piloto utiliza los únicos 25 hechos de producción ya consumidos. El segundo lote de 25 curiosidades tiene imágenes descargadas, pero sigue pendiente de aprobación; no equivale a un episodio listo.

**No puede garantizarse el 100 % de publicaciones** solo mediante un cron de GitHub y una investigación diaria: intervienen la calidad de fuentes, derechos, límites de servicios, OAuth, disponibilidad de YouTube y eventuales cambios de políticas.

## Estrategia práctica

1. Elaborar **más contenido del que se consume**. Una publicación diaria agota 25 hechos por día, equivalentes a 175 hechos por semana. Si la preparación produce solo 25 hechos diarios, la reserva nunca crece.
2. Alcanzar una reserva inicial de **30 vídeos completamente aprobados** (750 datos e imágenes) antes de prometer continuidad. Meta ideal: 60 días (1.500 datos), con alerta crítica bajo 7 días.
3. Investigar y generar propuestas en lotes, pero solo considerar disponibles los que tengan contenido contrastado, imágenes pertinentes, licencia y créditos revisados, sin repeticiones.
4. Seleccionar grupos de 25 por tema y título compartidos. El módulo curio25.queue se usa tanto en el preflight como en el constructor.
5. Dos oportunidades de render al día, siempre para el mismo identificador y con historial de reservas para evitar repetición. GitHub puede omitir un cron: esto reduce riesgos pero no los elimina.
6. Vigilar cada día el inventario mediante el workflow annual-coverage.yml: informe JSON/Markdown, estado CRITICAL/AT_RISK/BUFFERED y una única incidencia GitHub que se actualiza, evitando decenas de avisos repetidos.
7. Con la autorización del propietario y OAuth del canal existente, preparar y **programar con antelación en YouTube** varias semanas de vídeos ya aprobados. Una vez programados en la plataforma, un problema puntual de GitHub no debería impedir el estreno de ese contenido.
8. Diseñar archivado y copias de seguridad para MP4s/fotos; los artefactos temporales de GitHub Actions caducan, y no conviene guardar cientos de gigabytes en Git.

## Cuánto esfuerzo requiere construir la reserva

Para publicar diariamente **y aumentar la reserva en 30 días hasta 30 episodios**, se necesitarían en promedio **50 datos aprobados y sus imágenes al día** durante ese periodo: 25 para la publicación y otros 25 para ahorrar. Es una carga editorial importante. La prioridad debe ser exactitud, originalidad y licencias, no llenar el contador con historias inventadas.

## Diagnóstico automático

Ejecutar: python -m curio25.coverage

Genera build/annual-coverage/coverage.json y coverage.md. Informa del número de episodios listos, los candidatos pendientes, la falta para el colchón de 30 días y el estado de OAuth. El campo confirmed_public_uploads es deliberadamente nulo hasta disponer de conciliación real con YouTube; nunca se inventa el éxito de una subida.

## Qué sigue bloqueado

- Aprobación real del lote de 25 candidatos y los medios, con revisión editorial y legal.
- Canal YouTube conectado y autorización OAuth del propietario. Publication_enabled continúa en false.
- Prueba de carga privada, conciliación tras errores y calendario de varios vídeos ya programados. **No se ha activado ninguna publicación.**
- Pipeline editorial de investigación **y aprobación** que suministre al menos 175 datos revisados por semana sin gasto de servicios.

Las funciones del monitor no crean hechos, no aprueban material dudoso, no desbloquean YouTube y no tocan UMBRAL.
