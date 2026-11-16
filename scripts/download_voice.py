"""Download exact approved voice binaries, fail on upstream changes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from curio25.sources import session
from curio25.state import sha
base='https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/'
files={'es_ES-davefx-medium.onnx':'d2c9224e122321aac3c33343957fff4d0f465226cb74c66b0f520ca3f8c0dd07','es_ES-davefx-medium.onnx.json':'531c4051502e1acbc10b42437f11679bfce9e3919e1796e51fabd73e01e7fd2e'}
root=Path(__file__).resolve().parents[1]/'models'; root.mkdir(exist_ok=True)
for name,digest in files.items():
    path=root/name
    if not path.exists():
        r=session().get(base+name,timeout=180); r.raise_for_status(); temporary=path.with_suffix(path.suffix+'.part'); temporary.write_bytes(r.content)
        if sha(temporary)!=digest: temporary.unlink(); raise ValueError('Modelo cambiado: revisar licencia y aprobar nuevo hash')
        temporary.replace(path)
    if sha(path)!=digest: raise ValueError('Integridad del modelo incorrecta')
print('Voz verificada')
