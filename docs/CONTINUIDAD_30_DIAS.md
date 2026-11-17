# Curio25 — investigación y calendario anticipado

## Suministro de contenido sin repetición

El workflow `.github/workflows/candidate-research.yml` ya no vuelve automáticamente al lote fijo del 17/11. Al detectar un archivo nuevo `data/candidates/AAAA-MM-DD.json`, `curio25.candidate_queue` busca **el lote más antiguo de 25 candidatos aún sin archivo de investigación**. Se ejecuta al recibir nuevos candidatos y en dos comprobaciones diarias de respaldo. Un día sin candidatos termina correctamente sin usar red ni abrir solicitudes de cambio duplicadas.

La investigación genera evidencias y propuestas de imágenes, pero **no aprueba hechos, fotos ni licencias**. El siguiente paso sigue siendo la revisión editorial y visual; no se puede eludir para llenar la reserva artificialmente.

## Calendario anticipado y horario correcto

`python -m curio25.calendar` crea `build/annual-coverage/calendar.json` para los próximos 30 días. Con `Europe/Madrid` y `18:00`, cada fecha conserva su hora local de publicación; el UTC cambia cuando cambia el horario de verano/invierno. Las pruebas cubren marzo y octubre de 2027.

La simulación distingue entre datos aprobados sin render, faltantes y episodios que **figuran** como programados en el historial. Nada de esto prueba por sí mismo que YouTube haya publicado o programado el vídeo.

El monitor anual adjunta ese calendario al informe diario y sigue avisando si el stock aprobado es inferior a 30 episodios.

## Condiciones pendientes para una operación anual

1. 25 hechos originales por vídeo, con fuentes contrastadas e imagen legalmente utilizable.
2. Mantener 30–60 días de material terminado, no solo un calendario de casillas.
3. Conectar el canal existente por OAuth y probar una carga privada autorizada.
4. Tras la aprobación explícita de publicación, programar vídeos anticipadamente en YouTube y conciliar los IDs de vídeos para no duplicar subidas. **Aún no se ha habilitado.**
5. Resguardar MP4s y metadatos en un almacenamiento persistente fuera de los artefactos caducables de GitHub.

El cron y el monitoreo reducen riesgo; no pueden garantizar que los servicios externos estén disponibles todos los días.
