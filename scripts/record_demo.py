"""Record two actual Webots scenarios and validate video plus event assertions."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEBOTS=os.environ.get('WEBOTS_BIN') or shutil.which('webots') or '/Applications/Webots.app/Contents/MacOS/webots'
def main():
    subprocess.run([sys.executable,'scripts/generate_worlds.py'],cwd=ROOT,check=True)
    reports=[]
    for name,world in [('workflow','demo_video'),('resilience','resilience_video')]:
        p=ROOT/'results'/f'{name}_recording.json';p.unlink(missing_ok=True)
        r=subprocess.run([WEBOTS,'--batch','--mode=fast','--stdout','--stderr',f'worlds/delivery_box_{world}.wbt'],cwd=ROOT,capture_output=True,text=True,timeout=240)
        if r.returncode or not p.exists() or not json.loads(p.read_text())['passed']:
            print(r.stdout);print(r.stderr);raise SystemExit(f'{name} recording or scenario failed; inspect {p}')
        path=ROOT/'output/raw'/f'{name}.mp4'
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,nb_frames','-show_entries','format=duration,size','-of','json',str(path)],text=True))
        s=probe['streams'][0]
        valid=s['codec_name']=='h264' and s['width']==1920 and s['height']==1080 and int(s['nb_frames'])>900
        reports.append({'name':name,'passed':valid,'metadata':probe})
        print(f'{name}: encoded and scenario assertions passed',flush=True)
    (ROOT/'results/video_validation.json').write_text(json.dumps({'passed':all(r['passed'] for r in reports),'videos':reports},indent=2))
    return 0 if all(r['passed'] for r in reports) else 1
if __name__=='__main__':raise SystemExit(main())
