# Recuperación de renders, sin publicar

El workflow elige un identificador diario una sola vez en Europe/Madrid. Si existe una única reserva previa de producción intacta, reanuda esa fecha y exactamente sus 25 hechos. Una carga incierta, una reserva de piloto, una fecha futura o varias reservas ambiguas detienen la ejecución. Un render atrasado no se reprograma como publicación de otro día.

Antes del render diario se guarda la reserva en main y se exige que el push termine correctamente. La confirmación de render se guarda únicamente después del éxito del render y de la subida del artefacto de Actions; un fallo de runner o de almacenamiento deja la reserva recuperable. No hay paso de YouTube upload. Los artefactos del repositorio público no son almacenamiento privado ni permanente; caducan a los siete días. Un render confirmado cuyo artefacto caduque sigue necesitando una revisión/recuperación explícita, no una nueva reserva.

Se añade un job de pruebas de recuperación sin dependencias de multimedia; no sustituye la suite completa ni el render final. Los comandos de pruebas no usan OAuth.