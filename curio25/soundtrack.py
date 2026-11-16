"""Curio25 original light-pop soundtrack, synthesized locally.

No commercial samples, borrowed melodies or recordings. Arrangement favors
soft plucked tones, bouncing bass and brushed percussion over arcade beeps.
"""
from __future__ import annotations
from pathlib import Path
import wave
import numpy as np

RATE=22050
BPM=116
MELODY=(72,74,76,-1,79,76,74,-1, 76,79,81,-1,79,76,74,-1,
        72,76,79,76,74,-1,72,-1, 74,76,72,-1,69,72,74,-1)
ROOTS=(65.406,97.999,110.0,87.307)  # C, G, A, F; common chords, new melody.


def _section(t,seconds):
    """A short, continuous chunk; use bounded RAM for five-minute music."""
    beat=60.0/BPM
    beat_phase=np.mod(t,beat)
    beat_num=np.floor(t/beat).astype(np.int64)
    eighth=beat/2
    note_age=np.mod(t,eighth)
    n_idx=np.floor(t/eighth).astype(np.int64)
    # Four melodic arrangements; rhythmic rests prevent constant bleeps.
    section=(np.floor(t/48).astype(np.int64))%4
    notes=np.asarray(MELODY,dtype=np.float64)[(n_idx+section*5)%len(MELODY)]
    note_hz=440.0*np.exp2((np.maximum(notes,0)-69.0)/12.0)
    pluck_env=np.exp(-7.8*note_age)
    # A mellow struck-pluck timbre and slightly detuned second partial.
    pluck=(notes>=0)*pluck_env*(np.sin(2*np.pi*note_hz*note_age)
          +.17*np.sin(4.01*np.pi*note_hz*note_age)
          +.05*np.sin(5.97*np.pi*note_hz*note_age))
    pluck*=np.where(section==2,.085,.10)

    root=np.asarray(ROOTS)[(beat_num//8)%4]
    bass=.098*np.sin(2*np.pi*root*t)*np.exp(-3.8*beat_phase)
    # Quiet chord warmth, ducked further under narration by FFmpeg.
    upper=np.asarray((1.25,1.50,1.20,1.333))[(beat_num//8)%4]*root
    pad=.025*(np.sin(2*np.pi*upper*t)+.4*np.sin(2*np.pi*root*.5*t))
    # Drum components made from oscillators; no downloaded drum sample.
    kick=.14*np.sin(2*np.pi*(76*beat_phase-8*beat_phase**2))*np.exp(-33*beat_phase)
    clap=.060*np.sin(2*np.pi*7200*t)*np.sin(2*np.pi*8700*t)*np.exp(-29*beat_phase)
    kick*=((beat_num%4)==0) | ((beat_num%4)==2)
    clap*=((beat_num%4)==1) | ((beat_num%4)==3)
    hat_age=np.mod(t,eighth)
    hat=.035*np.sin(2*np.pi*9800*t)*np.exp(-56*hat_age)
    # 8-bar changes: some phrases use no lead, keeping room for storytelling.
    space=np.where((beat_num//8)%8==7,.35,1.0)
    out=space*pluck+bass+pad+kick+clap+hat
    fade=np.clip(t/.3,0,1)*np.clip((seconds-t)/1.1,0,1)
    return np.clip(out*fade,-.36,.36)


def original_music(path, seconds=300.0):
    if not 1<=seconds<=360:
        raise ValueError("Duración musical fuera de rango")
    total=round(seconds*RATE)
    chunk=RATE*4
    path=Path(path)
    with wave.open(str(path),'wb') as f:
        f.setparams((1,2,RATE,0,'NONE','not compressed'))
        for start in range(0,total,chunk):
            n=min(chunk,total-start)
            t=(start+np.arange(n,dtype=np.float64))/RATE
            samples=_section(t,seconds)
            f.writeframes((samples*32767).astype('<i2').tobytes())


def lively_mix_filter():
    """Audible on breaks; automatically dips underneath spoken sentences."""
    return (
        "[0:a]loudnorm=I=-17:TP=-2:LRA=9,asplit=2[vmain][vside];"
        "[1:a]volume=0.93,highpass=f=45,lowpass=f=11500[music];"
        "[music][vside]sidechaincompress=threshold=0.052:ratio=6:"
        "attack=16:release=360:makeup=1[ducked];"
        "[vmain][ducked]amix=inputs=2:duration=first:normalize=0,"
        "alimiter=limit=0.92[a]"
    )
