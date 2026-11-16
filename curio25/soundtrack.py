"""Original upbeat instrumental for Curio25, rendered from synthesized tones.

This creates no copy of another channel's music, melody or sound recordings.
"""
from __future__ import annotations
import wave
from pathlib import Path
import numpy as np

RATE = 22050
BPM = 124
# An original, bouncy major-key tune, with silence slots to avoid crowding speech.
MELODY = (72, 76, 79, -1, 81, 79, 76, 74,
          72, -1, 76, 79, 74, 76, 72, -1,
          76, 79, 84, -1, 81, 79, 76, 74,
          77, -1, 74, 76, 72, 74, 76, -1)


def original_music(path, seconds=300.0):
    if not 1 <= seconds <= 360:
        raise ValueError("Duración de la música fuera de rango")
    n = round(RATE*seconds)
    t = np.arange(n, dtype=np.float64)/RATE
    beat = 60.0/BPM
    beat_number = t/beat
    beat_phase = np.mod(t,beat)
    eighth = beat/2.0
    note_phase = np.mod(t,eighth)
    note_ids = (t/eighth).astype(np.int64) % len(MELODY)
    notes = np.asarray(MELODY, dtype=np.float64)[note_ids]
    freq = 440.0*np.exp2((np.maximum(notes, 0)-69)/12)
    note_env = np.exp(-8.0*note_phase)
    pluck = (notes>=0)*(np.sin(2*np.pi*freq*note_phase) +
                          .21*np.sin(4*np.pi*freq*note_phase))*note_env*.18

    roots = np.asarray([65.406, 97.999, 110.0, 87.307])
    chord = ((beat_number//4).astype(np.int64))%4
    bass_freq = roots[chord]
    bass = .11*np.sin(2*np.pi*bass_freq*t)*(.72+.28*np.cos(2*np.pi*beat_phase/beat))

    # Fresh synthesized kick, clap and hi-hat, deterministic without samples.
    beat_step = (beat_number.astype(np.int64)) % 4
    kick_env = np.exp(-28*beat_phase)
    kick = (beat_step%2==0)*kick_env*.19*np.sin(2*np.pi*(72*beat_phase-13*beat_phase**2))
    clap_env = np.exp(-34*beat_phase)
    clap_noise = np.sin(2*np.pi*7331*t)*np.sin(2*np.pi*9007*t)
    clap = (beat_step%2==1)*clap_env*clap_noise*.095
    hat = .052*np.exp(-58*note_phase)*np.sin(2*np.pi*11271*t)
    # A gentle synth bell at each roughly 12-second chapter marker.
    chime_phase = np.mod(t,12)
    chime = .06*np.exp(-6*chime_phase)*np.sin(2*np.pi*880*chime_phase)

    output = pluck+bass+kick+clap+hat+chime
    # No arbitrary clipping and no recordings borrowed from other creators.
    peak = np.max(np.abs(output))
    output = output*(.31/max(.31,peak))
    fades = np.clip(t/.22, 0, 1)*np.clip((seconds-t)/1.2, 0, 1)
    output = np.clip(output*fades,-.36,.36)
    pcm = (output*32767).astype("<i2")
    with wave.open(str(Path(path)),"wb") as fd:
        fd.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        fd.writeframes(pcm.tobytes())


def lively_mix_filter():
    """Raised instrumental bed, dynamically ducked only while the narrator speaks.

    Intro/outro have no narration, so the music swells naturally. Main voice
    stays at the existing -17 LUFS target and peaks are limited.
    """
    return (
        "[0:a]loudnorm=I=-17:TP=-2:LRA=9,asplit=2[vmain][vside];"
        "[1:a]volume=0.88,highpass=f=55,lowpass=f=12000[music];"
        "[music][vside]sidechaincompress=threshold=0.055:ratio=5:"
        "attack=18:release=320:makeup=1[ducked];"
        "[vmain][ducked]amix=inputs=2:duration=first:normalize=0,"
        "alimiter=limit=0.92[a]"
    )
