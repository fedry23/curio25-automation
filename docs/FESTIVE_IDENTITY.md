# Curio25 Fiesta — identidad audiovisual original

El rediseño sigue el orden solicitado: intro, paleta/tipografía, reloj, escenas, outro y preview. Es una identidad propia construida por código: papel redondeado, cronómetro ilustrado, confeti y colores por categoría. No se han usado logos, capturas, música, animaciones ni plantillas de XpressTV.

## Intro · 2,4 segundos

60 fotogramas originales generados con Pillow: gradiente cielo/turquesa, tarjetas con entrada por escala, aparición escalonada de CURIO25, subtítulo «25 curiosidades en 5 minutos», cronómetro ilustrado, estrellas, burbujas y confeti que gira y cae. Se compone en x64,y160,w1792,h640: no invade la cabecera con el reloj real ni la franja de subtítulos. El cronómetro grande representa el reto de cinco minutos; el widget superior muestra el tiempo transcurrido real.

## Paleta y tipografía

Amarillo #FFD84D, turquesa #35D6C6, cielo #55B7FF, naranja #FF8A3D, fucsia #FF5FB2, violeta #7A6CFF, lima #B8EF55. Blanco y marino #183153 se usan para separar y contrastar. Nunito SemiBold600 y Black900 están incluidas bajo SIL OFL1.1, con licencia y procedencia en `assets/fonts/`. No hacen falta descargas de fuentes en los runners.

Los símbolos circulares se rasterizan con DejaVu para evitar glifos ausentes; los tests los comparan con el glifo de sustitución. Los subtítulos usan Nunito con `fontsdir` explícito y se comprueba su caja rasterizada real con FFmpeg/libass. El texto principal y los subtítulos tienen contraste alto; las combinaciones principales con texto marino superan4,5:1, salvo el violeta, reservado a elementos grandes con contraste superior a3:1.

## Reloj y escenas

Se conserva el cálculo del reloj continuo y su box independiente, con una cápsula amarilla, esfera blanca, borde violeta, dígitos Nunito y marcador naranja animado. No se reinicia al cambiar de curiosidad.

Cada categoría tiene su pareja cromática: animales turquesa/lima, ciencia cielo/violeta, historia amarillo/naranja, tecnología cielo/fucsia, naturaleza lima/turquesa. Los títulos viven en tarjetas blancas redondeadas con sombra suave; el panel de imagen crece y tiene movimiento de cámara, máscara redondeada y marco de color. Burbujas flotantes animadas permanecen en los márgenes. Las transiciones claras duran0,14s, sin fondos negros ni efectos estroboscópicos.

Las fotos y los datos son los mismos candidatos ya presentes en staging. No se han investigado, aprobado ni sustituido por otros automáticamente. El preview mantiene «BORRADOR — NO PUBLICAR».

## Outro · 2,6 segundos

65 fotogramas con el mismo lenguaje visual, acentos amarillo/fucsia y confeti animado. Textos: «¡Se acabó el tiempo!» y «¡Nos vemos mañana!». Sin invadir subtítulos ni el reloj real. Intro y outro ocupan los cinco segundos ya reservados en el programa, no se concatenan fuera del total.

## Voz, música y duración

Se conservan `voice_style.py`, `soundtrack.py` y la configuración existente: voz masculina española entusiasta, música original y ducking que baja la música durante la narración. Intro y outro, sin voz, permiten recuperar nivel musical. No se usan APIs ni servicios de pago. El presupuesto temporal se reparte a25fps dentro de300s; el MP4 final se valida contra300±5s y conserva25datos. La medición del borrador es299,971s. Los tiempos de subtítulos se derivan de cada WAV.

## Reproducir sin consumir producción

```bash
python -m curio25.preview --out build/festive-identity
pytest -q
python -m curio25 validate --out build/festive-identity
```

Usar el módulo `preview`, no `build` ni `revise`, para un borrador sin escritura de historial. La ruta no importa ni llama a YouTube, no aprueba candidatos ni imágenes y no modifica configuración, catálogo o SQLite de producción. `preview-manifest.json` mantiene `publishable:false`, cero datos verificados para publicación y cero imágenes aprobadas. Los tests y una comparación SHA256 antes/después complementan esta separación.

La estética familiar no cambia automáticamente la declaración de audiencia ni ningún ajuste de publicación. La evaluación editorial, de derechos, de voz y de audiencia del episodio sigue pendiente.
