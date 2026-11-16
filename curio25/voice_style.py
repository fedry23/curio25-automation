"""Modestly expressive, upbeat Spanish TTS using the existing free Piper model.

No voice cloning or imitation. Production still needs human listening checks.
"""
from __future__ import annotations


def vocal_profile(style: str, scene: int, chunk: int, count: int, text: str = '') -> dict:
    if not 0<=scene<25 or not 0<=chunk<count:
        raise ValueError("Índices de narración incorrectos")
    if style=="neutral":
        return dict(length_scale=1.0)
    if style=="entusiasta":
        # Light prosody cues; Piper has no reliable actor-style emotion control.
        phrase=text.strip()
        expressive = bool(phrase.startswith("¿") or "¡" in phrase)
        scene_offset=(0.0, 0.010, -0.005, 0.015)[scene%4]
        speed_offset=-0.010 if expressive else 0.0
        # Shorter openings with varied timing; Piper is not a fully emotional TTS.
        if count==1:
            return dict(length_scale=.935+scene_offset+speed_offset,noise_scale=.77,noise_w_scale=.88)
        if chunk==0:
            return dict(length_scale=.94+scene_offset+speed_offset,noise_scale=.79,noise_w_scale=.89)
        if chunk==count-1:
            return dict(length_scale=.95+scene_offset+speed_offset,noise_scale=.78,noise_w_scale=.87)
        return dict(length_scale=.975+scene_offset+speed_offset,noise_scale=.73,noise_w_scale=.82)
    if style!="alegre":
        raise ValueError("Estilo de voz desconocido")
    if count==1:
        return dict(length_scale=.955,noise_scale=.71,noise_w_scale=.86)
    if chunk==0:
        return dict(length_scale=.95,noise_scale=.72,noise_w_scale=.88)
    if chunk==count-1:
        return dict(length_scale=.94,noise_scale=.72,noise_w_scale=.88)
    return dict(length_scale=.985,noise_scale=.69,noise_w_scale=.80)


# These substitutions affect ONLY the audio input; subtitles keep proper spelling.
# Do not phoneticize scientific terms in source claims or video metadata.
def for_speech(text: str) -> str:
    import re
    replacements = {
        r"\bNOAA\b": "noa",
        r"\bWright\b": "Ráit",
        r"\bYellowstone\b": "Yélouston",
    }
    for pattern,spoken in replacements.items():
        text=re.sub(pattern,spoken,text)
    return text
