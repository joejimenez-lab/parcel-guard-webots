"""Validate every exported frame, create local posters and an inline GIF preview."""
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'
reports=[]
for mode,title,expected in [('workflow','Delivery Workflow',1249),('resilience','Security Recovery',1633)]:
    p=OUT/f'Parcel Guard - {title}.mp4'
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,nb_frames,r_frame_rate','-show_entries','format=duration,size','-of','json',str(p)],text=True))
    s=info['streams'][0]
    decoded=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True)
    ok=(s['codec_name']=='h264' and s['width']==1600 and s['height']==900 and int(s['nb_frames'])==expected
        and s['r_frame_rate']=='30/1' and decoded.returncode==0 and not decoded.stderr.strip())
    reports.append({'name':title,'passed':ok,'metadata':info,'all_frames_decoded_without_errors':decoded.returncode==0 and not decoded.stderr.strip()})
    poster=OUT/f"Parcel Guard {'Workflow' if mode=='workflow' else 'Recovery'} Poster.jpg"
    subprocess.run(['ffmpeg','-v','error','-ss','11.7' if mode=='workflow' else '38','-i',str(p),'-frames:v','1','-q:v','2','-y',str(poster)],check=True)
    print(f'{title}: {info["format"]["duration"]} s, {s["nb_frames"]} frames, validated',flush=True)
if not all(r['passed'] for r in reports):raise SystemExit('An exported video did not validate')
gif=OUT/'Parcel Guard Preview.gif'
subprocess.run(['ffmpeg','-v','error','-ss','4','-t','32','-i',str(OUT/'Parcel Guard - Delivery Workflow.mp4'),'-filter_complex','[0:v]fps=10,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=3','-loop','0','-y',str(gif)],check=True)
(ROOT/'results/render_validation.json').write_text(json.dumps({'passed':True,'videos':reports,'preview_bytes':gif.stat().st_size},indent=2))
print(f'Inline preview: {gif.stat().st_size/1e6:.1f} MB')
