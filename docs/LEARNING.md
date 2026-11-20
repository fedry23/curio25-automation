# Aprendizaje experimental de Curio25

Este módulo consulta canales de terceros solamente mediante YouTube Data API, conserva los campos originales en memoria y exige 30 canales distintos (15 descubiertos mediante consultas en español y 15 en inglés). La búsqueda regional no verifica nacionalidad. No infiere retención, no descarga ni analiza audio de terceros, no copia contenido y no crea rankings combinando propietarios. No se guardan estadísticas de terceros en el repositorio público. Un error o una muestra insuficiente dejan el perfil base.

El experimento del propio canal usa exclusivamente YouTube Analytics autorizado, el porcentaje medio visto de cada vídeo, ventanas de siete días y mínimos de 100 vistas y cinco vídeos por perfil. Alterna dos perfiles de voz ya existentes, conserva el perfil aplicado en el historial y solo favorece la variante si mejora la mediana al menos tres puntos; si deja de hacerlo, vuelve al perfil base. Es una regla exploratoria, no una prueba causal ni una garantía de mejora. El generador conserva los controles editoriales, técnicos y de publicación.

La configuración queda desactivada: exige consentimiento y OAuth específico de solo lectura, comprobación del canal y aceptación de las condiciones de analítica aplicables. No habilitar ni almacenar tokens, métricas o informes privados en Git. No publica vídeos ni cambia la aprobación del MP4. Las pruebas con API simulada no acreditan una consulta real.

Fuentes oficiales: https://developers.google.com/youtube/terms/developer-policies y https://developers.google.com/youtube/analytics/reference/reports/query.
