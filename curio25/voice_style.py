"""Modestly expressive, upbeat Spanish TTS using the existing free Piper model.

No voice cloning or imitation. Production still needs human listening checks.
"""
from __future__ import annotations


def vocal_profile(style: str, scene: int, chunk: int, count: int) -> dict:
    if not 0<=scene<25 or not 0<=chunk<count:
        raise ValueError("Índices de narración incorrectos")
    if style=="neutral":
        return dict(length_scale=1.0)
    if style=="entusiasta":
        # Shorter openings with varied timing; Piper is not a fully emotional TTS.
        if count==1:
            return dict(length_scale=.925,noise_scale=.78,noise_w_scale=.92)
        if chunk==0:
            return dict(length_scale=.925,noise_scale=.80,noise_w_scale=.92)
        if chunk==count-1:
            return dict(length_scale=.935,noise_scale=.79,noise_w_scale=.91)
        return dict(length_scale=.97,noise_scale=.73,noise_w_scale=.84)
    if style!="alegre":
        raise ValueError("Estilo de voz desconocido")
    if count==1:
        return dict(length_scale=.955,noise_scale=.71,noise_w_scale=.86)
    if chunk==0:
        return dict(length_scale=.95,noise_scale=.72,noise_w_scale=.88)
    if chunk==count-1:
        return dict(length_scale=.94,noise_scale=.72,noise_w_scale=.88)
    return dict(length_scale=.985,noise_scale=.69,noise_w_scale=.80)
