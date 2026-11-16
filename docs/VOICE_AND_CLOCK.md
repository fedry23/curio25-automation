# Voz alegre y reloj propio de Curio25

El canal usa la energía de los vídeos de curiosidades como referencia general,
sin clonar la voz, los textos, la música ni los diseños concretos de otros canales.

Voz: el nuevo perfil de config.json voice_delivery="alegre" añade variaciones
moderadas de ritmo, pausas naturales y parámetros acústicos por fragmento
narrado. El perfil neutral conserva la locución sin cambios. Se sigue usando
la voz libre Piper es_ES-davefx. El resultado puede sonar más dinámico, pero
Piper no es un actor de voz con controles emocionales; antes de publicar
siempre se debe escuchar el vídeo entero y revisar expresividad y claridad.
Las marcas temporales de los subtítulos se obtienen del audio final de cada
fragmento, no se adivinan.

Reloj: en la cabecera derecha hay una esfera propia con punto luminoso que
da una vuelta por cada episodio de cinco minutos y números que avanzan desde
00:00 hasta 05:00. El cálculo usa la posición temporal real de cada escena,
por lo que no se reinicia al pasar de curiosidad. El rótulo se mantiene
fuera de la caja del título y de la franja de subtítulos. El archivo
clock-report.json registra las 25 marcas de tiempo. El último medio segundo
muestra 05:00 para cerrar el reto visual de cinco minutos.

Sin publicación: tanto el render diario como el borrador de revisión continúan
con YouTube desactivado y se conservan las barreras de validación editorial.
