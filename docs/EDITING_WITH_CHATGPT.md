# Modificar Curio25 desde ChatGPT mediante GitHub

El proyecto está preparado para editar archivos y revisar cambios desde la integración GitHub; no necesita una API propia ni contraseñas dentro del repositorio.

## Conexión necesaria

Conceder acceso al nuevo repositorio `fedry23/curio25-automation` en la instalación GitHub conectada a ChatGPT. Si la aplicación tiene acceso solo a repositorios seleccionados, añadir este repositorio explícitamente. Poder leer UMBRAL no concede acceso a Curio25. La capacidad de crear repositorios es un permiso distinto: la integración disponible en esta sesión lo rechazó con 403; un repositorio vacío creado por el propietario permite continuar si la aplicación tiene acceso de escritura.

## Cambios seguros por archivo

| Petición | Archivo principal |
|---|---|
| Cambiar hora de publicación futura | `config.json`: `publish_hour`, `timezone` |
| Mejorar redacción o humor | `data/facts.json`: `narration`, conservar evidencias |
| Añadir curiosidades | `data/facts.json` + capturas y revisión de fuentes |
| Sustituir una fotografía | `data/media/assets.json`, imagen, registro de licencia |
| Ajustar estética y subtítulos | `curio25/layout.py`, `art.py`, `render.py` |
| Cambiar frecuencia de render | `.github/workflows/daily.yml` |

Ejemplo de petición: “En fedry23/curio25-automation, crea una rama para cambiar la hora a 19:30 Europe/Madrid. Mantén desactivada la publicación, ejecuta las pruebas y abre un PR”.

Ejemplo de contenido: “Mejora el humor de solar-014 sin cambiar sus afirmaciones. Conserva la fuente. Genera un piloto revisado y comprueba que siga durando 300±5 segundos y que las dos líneas de subtítulos no invadan las imágenes”.

## Revisión y pruebas

ChatGPT debe leer `AGENTS.md`, conservar el historial y usar cambios coherentes en una rama. El workflow `Tests` comprueba procedencia, licencias, duplicados, barreras de subida y layout. Los tests que dependen del MP4 completo requieren generar el vídeo; un PR sin render no prueba la composición final. El workflow diario admite ejecución manual para generar artefactos en nube, pero necesita un lote nuevo de 25 datos revisados si el catálogo ya está consumido.

Para revisar visualmente el piloto existente sin gastar nuevos datos, ejecutar localmente o en un runner autorizado:

```bash
python -m curio25 revise --episode pilot-001 --out build/pilot-002
python -m curio25 validate --out build/pilot-002
```

`revise` solo admite un episodio sin subir. Reemplaza su hash de producción y mantiene reservados los mismos25 datos. Se requiere volver a aprobar el MP4 si en el futuro se habilita publicación.

No guardar tokens en issues, conversaciones, configuraciones, commits ni logs. Las credenciales Google son secretos separados y no son necesarias para editar o renderizar. No activar publicación por una petición genérica de “automatizar” o “mejorar”; sigue pendiente la aprobación explícita del episodio y la conexión del canal.
