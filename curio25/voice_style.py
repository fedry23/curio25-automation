"""Modestly expressive, upbeat Spanish TTS using the existing free Piper model.

No voice cloning or imitation. Production still needs human listening checks.
"""
from __future__ import annotations


def vocal_profile(style: str, scene: int, chunk: int, count: int) -> dict:
    if not 0<=scene<25 or not 0<=chunk<count:
        raise ValueError("Índices de narración incorrectos")
    if style=="neutral":
        return dict(length_scale=1.0)
    if style!="alegre":
        raise ValueError("Estilo de voz desconocido")
    if count==1:
        return dict(length_scale=.955,noise_scale=.71,noise_w_scale=.86)
    if chunk==0:
        return dict(length_scale=.95,noise_scale=.72,noise_w_scale=.88)
    if chunk==count-1:
        return dict(length_scale=.94,noise_scale=.72,noise_w_scale=.88)
    return dict(length_scale=.985,noise_scale=.69,noise_w_scale=.80)
