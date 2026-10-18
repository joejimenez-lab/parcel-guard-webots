"""Copy verified raw footage and export only recorded telemetry for video overlays."""
import json
import shutil
import subprocess
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'demo-studio/public';PUBLIC.mkdir(exist_ok=True)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mode', choices=('workflow','resilience','all'), default='all')
mode=parser.parse_args().mode
for name in (('workflow','resilience') if mode=='all' else (mode,)):
    report=json.loads((ROOT/'results'/f'{name}_recording.json').read_text())
    if not report['passed']:raise SystemExit(f'{name}: scenario assertions failed')
    shutil.copy2(ROOT/report['raw_video'],PUBLIC/f'{name}.mp4')
    capture=json.loads((ROOT/'results'/f'{name}_interface_capture.json').read_text())
    if not capture['passed'] or report['interaction_source']!='live browser form and button handlers':
        raise SystemExit('The demo must be recorded through the live control page')
    shutil.copy2(ROOT/'output/raw'/f'{name}-interface.mp4',PUBLIC/f'{name}-interface.mp4')
    rows=[];previous=None
    for row in report['telemetry']:
        s=row['status']
        if s['time']==previous:continue
        previous=s['time']
        keys=('time','phase','secured','delivery_pending','fault','door','latch','parcel','link','pending','delivered_ids','endpoint_ids','events','parcel_distances_m','door_angle_rad','latch_position_m','motion_peak_m_s2','grant','endpoint_duplicate_packets')
        rows.append({'at':row['video_time_s'],'status':{k:s[k] for k in keys}})
    (PUBLIC/f'{name}.json').write_text(json.dumps({'chapters':report['chapters'],'samples':rows,'checks':report['checks']},separators=(',',':')))
for name in ('webots_classification','webots_sensor_trials','webots_benchmark'):
    shutil.copy2(ROOT/'results'/f'{name}.json',PUBLIC/f'{name}.json')
print('Prepared verified footage and synchronized telemetry')

benchmark=json.loads((PUBLIC/'webots_benchmark.json').read_text())['checks']
classification=json.loads((PUBLIC/'webots_classification.json').read_text())
sensor=json.loads((PUBLIC/'webots_sensor_trials.json').read_text())
summary={'presence':f"{sensor['correct']} / 50", 'f1':f"{classification['macro_f1']:.2f}",
         'falseAlarms':f"{classification['false_alarms']} / 45", 'cycles':f"{benchmark['motor_cycles']['successful']} / 100",
         'unauthorized':f"{benchmark['access_security']['unauthorized_unlocks']} / 30", 'recovered':f"{benchmark['connection_recovery']['recovered_events']} / 100",
         'observer':f"{benchmark['alert_latency']['max_stimulus_to_observer_s']:.3f}"}
(PUBLIC/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')

if mode in ('workflow', 'all'):
    subprocess.run(['ffmpeg','-v','error','-ss','8','-i',str(PUBLIC/'workflow.mp4'),'-frames:v','1','-q:v','2','-y',str(PUBLIC/'cover.jpg')],check=True)

# Labeled inspection pauses use exact frames from the live UI recording.
if mode in ('resilience', 'all'):
    subprocess.run(['ffmpeg','-v','error','-ss','7','-i',str(PUBLIC/'resilience-interface.mp4'),'-frames:v','1','-y',str(PUBLIC/'expired-code.png')],check=True)
    subprocess.run(['ffmpeg','-v','error','-ss','20.9','-i',str(PUBLIC/'resilience-interface.mp4'),'-frames:v','1','-y',str(PUBLIC/'drop-acks.png')],check=True)
