# Validación del rediseño Curio25 Fiesta

- **146 tests superados** localmente. Incluyen caja real de subtítulos con Nunito/libass, glifos ausentes, contraste, categorías, movimiento, áreas seguras y garantías del preview. Log en `examples/festive-identity/tests.txt`.
- MP4 real: **299,971s**, 1920×1080, H.264/AAC, decodificación estricta completa sin errores. Pico medido −0,8dBFS.
- SHA256: `5d0fc642494aee741e0aef2e5d7b10bc79510851f575d58497bab9913bc3a90d`.
- Intro original: 2,4s,60fotogramas. Outro:2,6s,65fotogramas. Ambos clips gráficos son1792×640 y se superponen sin ocupar reloj ni subtítulos. Las extracciones `intro-demo.mp4` y `outro-demo.mp4` permiten verlos con el audio y el encuadre reales.
- 25 escenas y25 curiosidades. Subtítulos de máximo2líneas; primer cue después de la intro; último cue antes de la outro. Reloj real continuo, comprobado visualmente en00:00 y05:00 (`clock-start.jpg`, `clock-end.jpg`).
- Revisados ocho fotogramas del MP4: intro, cinco categorías y cierre. También un preview640×360. El storyboard y `visual-review.json` conservan tiempos y selección.
- Se detectaron glifos decorativos ausentes en Nunito y se corrigieron antes del render final: símbolos DejaVu, tipografía de texto Nunito. No se entregan los renders intermedios descartados.

## Estado protegido

`protected-state.json` acredita comparación SHA256 antes/después de configuración, catálogo, JSON/SQLite de historial, candidatos y sus estados de revisión, módulo de publicación y código de estado/CLI. Ninguno cambió. Git tampoco muestra cambios en datos, configuración, `youtube.py`, `state.py`, `__main__.py`, `voice_style.py` o `soundtrack.py`.

El vídeo es **BORRADOR NO PUBLICABLE**: `preview-manifest.json` conserva25candidatos pendientes, cero hechos verificados para publicación, cero imágenes aprobadas y `publishable:false`. El render se ejecutó con `python -m curio25.preview`; no reserva episodios ni consume el historial. No se llamó a YouTube ni se modificó UMBRAL.

La inspección visual y las mediciones no sustituyen una escucha humana ni la revisión editorial/de derechos pendiente. El vídeo nuevo no supone aprobación de publicación. Fuentes Nunito redistribuidas con SIL OFL1.1; identidad gráfica, confeti y animaciones propios. Ningún recurso de XpressTV incorporado.
