"""Record two actual Webots scenarios and validate video plus event assertions."""
import json
import os
import shutil
import subprocess
import sys
import time
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEBOTS=os.environ.get('WEBOTS_BIN') or shutil.which('webots') or '/Applications/Webots.app/Contents/MacOS/webots'
def main():
    subprocess.run([sys.executable,'scripts/generate_worlds.py'],cwd=ROOT,check=True)
    reports=[]
    for name,world in [('workflow','demo_video'),('resilience','resilience_video')]:
        p=ROOT/'results'/f'{name}_recording.json';p.unlink(missing_ok=True)
        descriptor=ROOT/'.build/ui-capture'/f'{name}.json'
        descriptor.unlink(missing_ok=True)
        images=ROOT/'.build/ui-capture'/f'{name}-frames'
        if images.exists(): shutil.rmtree(images)
        log=(ROOT/'results'/f'{name}_capture.log').open('w')
        process=subprocess.Popen([WEBOTS,'--batch','--mode=fast','--stdout','--stderr',str(ROOT/'worlds'/f'delivery_box_{world}.wbt')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'PARCEL_GUARD_CAPTURE_UI':'1'})
        try:
            subprocess.run(['node','demo-studio/scripts/capture-interface.mjs',name,str(ROOT)],cwd=ROOT,check=True,timeout=900)
            code=process.wait(timeout=240)
        except BaseException:
            process.terminate()
            process.wait(timeout=30)
            raise
        finally:
            log.close()
        if code or not p.exists() or not json.loads(p.read_text())['passed']:
            raise SystemExit(f'{name} recording or scenario failed; inspect {p} and results/{name}_capture.log')
        subprocess.run(['ffmpeg','-v','error','-framerate','125/12','-i',str(images/'%05d.jpg'),'-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart','-y',str(ROOT/'output/raw'/f'{name}-interface.mp4')],check=True)
        capture_path=ROOT/'results'/f'{name}_interface_capture.json'
        capture=json.loads(capture_path.read_text())
        capture['artifact_sha256']={str(file.relative_to(ROOT)):hashlib.sha256(file.read_bytes()).hexdigest() for file in (
            ROOT/'output/raw'/f'{name}-interface.mp4',ROOT/'output/raw'/f'{name}.mp4',
            ROOT/'demo-studio/scripts/capture-interface.mjs',
            ROOT/'plugins/robot_windows/lockbox_window/lockbox_window.html')}
        capture_path.write_text(json.dumps(capture,indent=2)+'\n')
        path=ROOT/'output/raw'/f'{name}.mp4'
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,nb_frames','-show_entries','format=duration,size','-of','json',str(path)],text=True))
        s=probe['streams'][0]
        valid=s['codec_name']=='h264' and s['width']==1920 and s['height']==1080 and int(s['nb_frames'])>700
        reports.append({'name':name,'passed':valid,'metadata':probe})
        print(f'{name}: encoded and scenario assertions passed',flush=True)
        # Let macOS finish closing the native application before the next launch.
        time.sleep(4)
    (ROOT/'results/video_validation.json').write_text(json.dumps({'passed':all(r['passed'] for r in reports),'videos':reports},indent=2))
    return 0 if all(r['passed'] for r in reports) else 1
if __name__=='__main__':raise SystemExit(main())
