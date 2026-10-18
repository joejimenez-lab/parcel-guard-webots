"""Validate every exported frame, create local posters and an inline GIF preview."""
import json
import hashlib
import subprocess
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'

def repair_transition_picture(path, candidates):
    """Replace an isolated decoder-start blank with its preceding recorded frame."""
    def picture_fraction(frame):
        pixels = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
            '-vf', f'select=eq(n\\,{frame}),crop=1728:800:96:80,scale=216:100,format=gray',
            '-frames:v', '1', '-f', 'rawvideo', '-'])
        if len(pixels) != 21600:
            raise RuntimeError(f'Cannot inspect transition frame {frame}: {path.name}')
        return sum(value < 225 for value in pixels) / len(pixels)
    repaired = []
    for frame in candidates:
        if picture_fraction(frame) >= 0.005:
            continue
        if min(picture_fraction(frame - 1), picture_fraction(frame + 1)) < 0.005:
            raise RuntimeError(f'Multiple blank transition frames: {path.name}')
        stage = ROOT / '.build' / 'media-repair'
        stage.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, stage / f'{path.stem}-before-{frame}.mp4')
        temporary = stage / path.name
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-filter_complex',
            f'[0:v]split[a][b];[a][b]freezeframes=first={frame}:last={frame}:replace={frame-1}[v]',
            '-map', '[v]', '-an', '-c:v', 'libx264', '-crf', '16', '-preset', 'veryfast',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-y', str(temporary)], check=True)
        temporary.replace(path)
        repaired.append(frame)
    return repaired

reports=[]
for mode,title,expected in [('workflow','Delivery Workflow',1185),('resilience','Security Recovery',1533),('final','Final Demonstration',2508)]:
    p=OUT/f'Parcel Guard - {title}.mp4'
    repaired=repair_transition_picture(p, [121, 1036] if mode=='final' else [121])
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,nb_frames,r_frame_rate','-show_entries','format=duration,size','-of','json',str(p)],text=True))
    s=info['streams'][0]
    decoded=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True)
    ok=(s['codec_name']=='h264' and s['width']==1920 and s['height']==1080 and int(s['nb_frames'])==expected
        and s['r_frame_rate']=='30/1' and decoded.returncode==0 and not decoded.stderr.strip())
    reports.append({'name':title,'passed':ok,'path':str(p.relative_to(ROOT)),
                    'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'metadata':info,
                    'transition_picture_frames_repaired':repaired,
                    'all_frames_decoded_without_errors':decoded.returncode==0 and not decoded.stderr.strip()})
    poster=OUT/f"Parcel Guard {'Workflow' if mode=='workflow' else 'Recovery' if mode=='resilience' else 'Final'} Poster.jpg"
    subprocess.run(['ffmpeg','-v','error','-ss','11.5' if mode=='workflow' else '39.5' if mode=='resilience' else '11.5','-i',str(p),'-frames:v','1','-q:v','2','-y',str(poster)],check=True)
    print(f'{title}: {info["format"]["duration"]} s, {s["nb_frames"]} frames, validated',flush=True)
if not all(r['passed'] for r in reports):raise SystemExit('An exported video did not validate')
gif=OUT/'Parcel Guard Preview.gif'
subprocess.run(['ffmpeg','-v','error','-ss','4','-t','32','-i',str(OUT/'Parcel Guard - Delivery Workflow.mp4'),'-filter_complex','[0:v]fps=10,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=3','-loop','0','-y',str(gif)],check=True)
(ROOT/'results/render_validation.json').write_text(json.dumps({'passed':True,'videos':reports,'preview_bytes':gif.stat().st_size},indent=2))
print(f'Inline preview: {gif.stat().st_size/1e6:.1f} MB')
