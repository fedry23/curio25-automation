"""Video composition orchestrator for one 25-scene Curio25 episode.

Subtitles, FFmpeg inspection and episode metadata are separate tested modules.
Public imports are retained so older scripts and tests still work.
"""
import json
import logging
import subprocess
import wave
from pathlib import Path
from piper import PiperVoice
from piper.config import SynthesisConfig
from .art import panel, thumbnail, photo_layer, photo_frame
from .layout import caption_chunks,caption_layout,validate_scene,Box,PHOTO,PROGRESS,CAPTION_CENTER,CAPTION_FONT_SIZE,validate_animations
from .state import sha
from .clock import stopwatch_filters, clock_report
from .voice_style import vocal_profile,for_speech
from .branding import programme_lengths, INTRO_SECONDS, OUTRO_SECONDS
from .soundtrack import original_music, lively_mix_filter
from .theme import FONT_DIR,decorative_filters
from .festive_branding import render_brand_clip,render_frame
from .captions import stamp,ass_stamp,write_ass
from .video_io import run,probe,duration,validate
from .episode_meta import SOLAR_BODIES,episode_identity
LOG=logging.getLogger(__name__)
def allocate(lengths,target=300):
    if len(lengths)!=25: raise ValueError('25 segmentos obligatorios')
    minimum=sum(lengths)+.35*25
    if minimum>target: raise ValueError(f'Guion demasiado largo: {minimum:.1f}s. Editar texto; no acelerar voz.')
    pad=(target-sum(lengths))/25
    if pad>4.5: raise ValueError('Guion demasiado corto; añadir explicación editorial')
    return [v+pad for v in lengths]

def music(path,seconds):
    original_music(path,seconds)

def render(root,out,facts,config):
    root=Path(root); out=Path(out); out.mkdir(parents=True,exist_ok=True)
    topic,title=episode_identity(facts)
    confirmed=config.get('confirmed_publications_at_render')
    if confirmed is not None and (type(confirmed) is not int or confirmed<0):
        raise ValueError('Contador de publicaciones inválido')
    if any(f.get('preview_only') for f in facts): confirmed=None
    voice=PiperVoice.load(str(root/config['voice_model'])); sync=[]; lengths=[]
    style=config.get('voice_delivery','alegre')
    for idx,f in enumerate(facts):
        parts=[]; cursor=0; cues=[]
        chunks=caption_chunks(f['narration'])
        for j,sentence in enumerate(chunks):
            p=out/f'voice-{idx:02}-{j}.wav'
            settings=vocal_profile(style,idx,j,len(chunks),sentence)
            with wave.open(str(p),'wb') as w:
                voice.synthesize_wav(for_speech(sentence),w,syn_config=SynthesisConfig(**settings))
            with wave.open(str(p),'rb') as w: params=w.getparams(); data=w.readframes(w.getnframes()); seconds=w.getnframes()/w.getframerate()
            parts.append(data); cues.append((cursor,cursor+seconds,sentence)); cursor+=seconds
        with wave.open(str(out/f'voice-{idx:02}.wav'),'wb') as w: w.setparams(params); w.writeframes(b''.join(parts))
        lengths.append(cursor); sync.append(cues); LOG.info('Voz %s: %.2fs',f['id'],cursor)
    intro=INTRO_SECONDS if config.get('intro_enabled',True) else 0
    outro=OUTRO_SECONDS if config.get('outro_enabled',True) else 0
    durations=programme_lengths(lengths,config['target_seconds'],intro,outro)
    brand_clips={}
    for kind,seconds in [('intro',intro),('outro',outro)]:
        if seconds:
            clip=out/f'brand-{kind}.mp4'
            render_brand_clip(clip,kind=kind,seconds=seconds)
            render_frame(1.5,kind).save(out/f'{kind}-preview.png')
            brand_clips[kind]=clip
    frame_counts=[round(v*25) for v in durations]
    frame_counts[-1]+=round(config['target_seconds']*25)-sum(frame_counts)
    absolute=0; subtitles=[]; chapters=[]; segments=[]; layout_reports=[]
    for idx,(f,secs) in enumerate(zip(facts,durations)):
        LOG.info('Render %d/25',idx+1); elements=panel(f,idx+1,out/f'panel-{idx:02}.png')
        local=[]; ass_cues=[]; caption_boxes=[]
        narration_offset=intro if idx==0 else 0
        for start,end,text in sync[idx]:
            layout=caption_layout(text); display='\n'.join(layout['lines'])
            local_start=.15+narration_offset+start
            local_end=.15+narration_offset+end
            cue=f'{len(subtitles)+1}\n{stamp(absolute+local_start)} --> {stamp(absolute+local_end)}\n{display}\n'
            subtitles.append(cue); local.append(f'{len(local)+1}\n{stamp(local_start)} --> {stamp(local_end)}\n{display}\n')
            ass_cues.append((local_start,local_end,layout['lines']))
            caption_boxes.append(dict(**layout,start=local_start,end=local_end,timing='Measured duration of independently synthesized Piper chunk'))
        (out/f'captions-{idx:02}.srt').write_text('\n'.join(local))
        write_ass(out/f'captions-{idx:02}.ass',ass_cues)
        scene_report=validate_scene(elements,caption_boxes)
        scene_report.update(fact_id=f['id'],scene=idx+1,photograph=bool(f.get('media_path')),whole_frame_motion=False)
        if not scene_report['passed']: raise ValueError('Layout inválido: '+str(scene_report['errors']))
        layout_reports.append(scene_report)
        (out/'layout-report.json').write_text(json.dumps(dict(passed=all(r['passed'] for r in layout_reports),frame=[1920,1080],max_caption_lines=2,scenes=layout_reports),ensure_ascii=False,indent=2))
        frames=frame_counts[idx]; actual=frames/25
        scene_start=absolute
        chapters.append(dict(start=absolute,title=f['title'],fact_id=f['id'],source=f['source_url']))
        absolute+=actual
        fade='0xFFFDF5'
        # No zoom or pan of the full frame: titles/credits/captions stay pixel-fixed.
        # Animated dot remains inside its own progress track, above the caption band.
        motion=decorative_filters(idx)+f",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='•':fontsize=16:fontcolor=0x83e9df:x='94+724*t/{actual}':y=795"
        scene_report['animations']=[dict(name='progress_dot',envelope=[90,793,840,815],container=[90,790,840,820],inside_caption_band=False)]
        if f['graphic']['kind']=='orbit':
            motion+=",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='●':fontsize=24:fontcolor=white:x='1385+330*cos(t*0.6)-12':y='537+150*sin(t*0.6)-12'"
            scene_report['animations'].append(dict(name='orbit_marker',envelope=[1040,370,1730,705],container=list(PHOTO.tuple()),inside_caption_band=False))
        vf=f"fps=25,{motion},drawbox=x=0:y=840:w=1920:h=240:color=0xFFFDF5:t=fill,ass=filename=captions-{idx:02}.ass:fontsdir='{FONT_DIR}',fade=t=in:st=0:d=0.14:color={fade},fade=t=out:st={max(0,actual-.14)}:d=0.14:color={fade}"
        if config.get('stopwatch_enabled',True):
            vf+=','+stopwatch_filters(scene_start,config['target_seconds'])
            scene_report['animations'].append(dict(
                name='five_minute_clock_dot',envelope=[1380,66,1450,139],
                container=[1360,57,1662,145],inside_caption_band=False))
        if f.get('preview_only'):
            vf+=",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='BORRADOR - NO PUBLICAR':fontsize=18:fontcolor=0x183153:x=450:y=130:box=1:boxcolor=0xFFD84D@0.9:boxborderw=3"
        target=out/f'segment-{idx:02}.mp4'
        # Photo zoom/pan is clipped to a fixed PHOTO-sized layer before compositing.
        cmd=['ffmpeg','-y','-v','error','-threads','2','-loop','1','-framerate','25','-i',f'panel-{idx:02}.png','-i',f'voice-{idx:02}.wav']
        has_photo=photo_layer(f,out/f'photo-layer-{idx:02}.png')
        if has_photo:
            photo_frame(f,out/f'photo-frame-{idx:02}.png')
            cmd+=['-i',f'photo-layer-{idx:02}.png','-i',f'photo-frame-{idx:02}.png']
            pan=f"[2:v]zoompan=z='1.025+0.035*on/{frames}':x='(iw-iw/zoom)*on/{frames}':y='(ih-ih/zoom)/2':d={frames}:s={PHOTO.width}x{PHOTO.height}:fps=25[photo];[0:v][photo]overlay={PHOTO.x1}:{PHOTO.y1}:shortest=1[moving];[moving][3:v]overlay={PHOTO.x1}:{PHOTO.y1}[base];"
            next_input=4
            scene_report['animations'].append(dict(name='photo_camera',envelope=list(PHOTO.tuple()),container=list(PHOTO.tuple()),whole_frame_motion=False))
        else:
            pan=''; next_input=2
        base_label='base' if has_photo else '0:v'
        kind='intro' if idx==0 else 'outro' if idx==24 else None
        if kind in brand_clips:
            cmd+=['-i',brand_clips[kind].name]
            shift=0 if kind=='intro' else actual-outro
            seconds=intro if kind=='intro' else outro
            # The ident is clipped to OPEN_AREA; the global clock is painted afterwards.
            pan+=f'[{next_input}:v]setpts=PTS-STARTPTS+{shift}/TB[ident];[{base_label}][ident]overlay=64:160:eof_action=pass:repeatlast=0:enable=\'between(t,{shift},{shift+seconds})\'[branded];'
            base_label='branded'
            scene_report['branding']=dict(kind=kind,start=shift,duration=seconds,box=[64,160,1856,800],subtitle_overlap=False)
        if kind=='intro' and kind in brand_clips and confirmed is not None:
            # In the lower margin of the brand area, below both animated cards.
            vf+=f",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='Publicados antes {confirmed}':fontsize=28:fontcolor=white:box=1:boxcolor=0x183153@0.95:boxborderw=8:x=(w-tw)/2:y=746:enable='between(t,0,{intro})'"
            scene_report['publication_counter']={'confirmed_before_render':confirmed,'label':'Publicados antes','box':[620,730,1300,790]}
        complex_filter=pan+f'[{base_label}]{vf}[v];[1:a]adelay={round((.15+narration_offset)*1000)},apad,atrim=duration={actual}[a]'
        animation_errors=validate_animations(scene_report['animations'])
        scene_report['errors']+=animation_errors; scene_report['passed']=not scene_report['errors']
        if animation_errors: raise ValueError('Animación fuera de caja: '+str(animation_errors))
        cmd+=['-filter_complex',complex_filter,'-map','[v]','-map','[a]','-t',str(actual),'-c:v','libx264','-threads','2','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k',target.name]
        result=subprocess.run(cmd,cwd=out,capture_output=True,text=True)
        if result.returncode: raise RuntimeError(result.stderr[-4000:])
        segments.append(f"file '{target.name}'")
    (out/'layout-report.json').write_text(json.dumps(dict(passed=all(r['passed'] for r in layout_reports),frame=[1920,1080],max_caption_lines=2,scenes=layout_reports),ensure_ascii=False,indent=2))
    (out/'captions.srt').write_text('\n'.join(subtitles)); (out/'concat.txt').write_text('\n'.join(segments))
    if config.get('stopwatch_enabled',True):
        (out/'clock-report.json').write_text(json.dumps(
            clock_report(chapters,config['target_seconds']),ensure_ascii=False,indent=2))
    music(out/'music.wav',config['target_seconds'])
    result=subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i','concat.txt','-i','music.wav','-filter_complex',lively_mix_filter(),'-map','0:v','-map','[a]','-t','300','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart','episode.mp4'],cwd=out,capture_output=True,text=True)
    if result.returncode: raise RuntimeError(result.stderr[-4000:])
    thumbnail(out/'thumbnail.jpg',topic=topic,photo_path=facts[0].get('media_path')); report=validate(out/'episode.mp4'); (out/'validation.json').write_text(json.dumps(report,indent=2))
    desc=('Curiosidades del sistema solar explicadas con fotografías reales, gráficos originales y humor ligero.' if topic=='sistema solar' else f'25 datos curiosos originales sobre {topic}, con recursos acreditados y humor ligero.')+'\nNarración sintética en español de España (Piper davefx); diagramas esquemáticos originales, sin escala.\n\n'
    for c in chapters: desc+=f"{int(c['start'])//60:02}:{int(c['start'])%60:02} {c['title']}\n"
    desc+='\nFUENTES DOCUMENTALES:\n'+'\n'.join(sorted({f['source_url'] for f in facts}))
    if any(f.get('media_credit') for f in facts):
        from .media import credits
        desc+='\nIMÁGENES (licencias aptas para uso comercial; créditos por recurso):\n'+credits([f['media_record'] for f in facts if f.get('media_record')])+'\n'
    desc+='\n\nCRÉDITOS: Guion y diagramas originales Curio25. Música original generada por síntesis (sin muestras externas). Voz Piper davefx, conjunto CC0. Sin afiliación ni respaldo de las instituciones citadas.\n'
    if len(desc)>5000:
        if all(f.get('preview_only') for f in facts):
            (out/'full-attributions.txt').write_text(desc,encoding='utf-8')
            desc=('BORRADOR INTERNO - NO PUBLICAR. Fuentes y licencias completas '
                  'en full-attributions.txt, dentro del artefacto de revisión.')
        else:
            raise ValueError('Descripción supera el límite de YouTube; editar sin omitir atribuciones')
    (out/'description.txt').write_text(desc); (out/'script.json').write_text(json.dumps([dict(f,media_path='data/media/'+f['media_record']['file']) if f.get('media_record') else f for f in facts],ensure_ascii=False,indent=2))
    (out/'metadata.json').write_text(json.dumps(dict(title=title,description=desc,chapters=chapters,synthetic_voice=True,voice_profile=style,learning_decision=config.get('learning_decision','disabled'),contains_synthetic_media=False,preview_only=any(f.get('preview_only') for f in facts),confirmed_publications_at_render=confirmed,sha256=report['sha256']),ensure_ascii=False,indent=2))
    (out/'assets.json').write_text(json.dumps([dict(fact_id=f['id'],file=f'panel-{i:02}.png',author='Curio25',license='CC-BY-4.0',source='Composición original: curio25/art.py',photograph=('data/media/'+f['media_record']['file']) if f.get('media_record') else None,photograph_credit=f.get('media_credit'),original_media=f.get('media_record'),sha256=sha(out/f'panel-{i:02}.png')) for i,f in enumerate(facts)]+[dict(file='music.wav',author='Curio25',license='CC0-1.0',source='Síntesis original: curio25/render.py',sha256=sha(out/'music.wav'))],indent=2))
    return report
