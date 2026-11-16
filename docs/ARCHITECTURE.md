# Decisiones de arquitectura

1. Catálogo editorial JSON con fuentes y capturas verificables → selección de 25 datos no usados → reserva transaccional SQLite.
2. Guion original previamente revisado → Piper local por oración → duración real WAV y subtítulos. Distribuir las pausas hasta 300 s; rechazar extremos en lugar de acelerar la voz.
3. Especificación gráfica por dato → Pillow para diagramas → FFmpeg para cámara, órbitas/progreso animados, transiciones y rótulos → mezcla de voz normalizada, composición musical y acentos propios → MP4 y SRT.
4. Validar resolución, duración, volumen y decodificación completa → miniatura, descripción, capítulos y manifiesto de autoría.
5. Historial JSON versionado y SQLite para transacciones/sesión sensible. No eliminar reservas automáticamente si hubo un fallo.
6. Barrera de publicación por configuración, hash del vídeo aprobado y canal OAuth. Carga oficial reanudable; guardar ID antes de subir complementos. Fallar cerrado si el estado es incierto.

El planificador de Actions renderiza a diario sin necesitar un ordenador personal. No descubre ni verifica autónomamente nuevos hechos; requiere ampliar el catálogo editorial. Un modelo de lenguaje sin revisión y unas URLs no bastan como verificación. Se evita depender de APIs gratuitas ilimitadas: TTS y gráficos son locales; descargas de voz y recursos tienen caché/integridad y límites. No se usa Edge TTS como requisito porque depende de un servicio remoto sin garantía de disponibilidad o permisos de explotación estables para esta integración.

El piloto actualizado integra once fotografías de dominio público de Commons mediante un inventario aprobado y verificado por hash. Cada dato se vincula a una foto real del cuerpo celeste, con crédito en pantalla y atribución completa en manifiesto/descripción. La fotografía se anima dentro de su caja; no se mueve el plano completo. Una banda exclusiva de subtítulos queda fuera de todas las cajas visuales. No hay coste de stock ni contenido de derechos inciertos.

## Operación antes de ampliar

Añadir una cola de episodios revisados por hash, catálogo de cientos de datos, copias duraderas de vídeos y estado, y conciliación de subidas interrumpidas. Probar OAuth con el canal real y evaluar pronunciación/ritmo con el usuario. No relajar las barreras para convertir el piloto en publicación masiva.
