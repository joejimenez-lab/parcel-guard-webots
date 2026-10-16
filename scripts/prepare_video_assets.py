"""Copy verified raw footage and export only recorded telemetry for video overlays."""
import json
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'demo-studio/public';PUBLIC.mkdir(exist_ok=True)
for name in ('workflow','resilience'):
    report=json.loads((ROOT/'results'/f'{name}_recording.json').read_text())
    if not report['passed']:raise SystemExit(f'{name}: scenario assertions failed')
    shutil.copy2(ROOT/report['raw_video'],PUBLIC/f'{name}.mp4')
    rows=[];previous=None
    for row in report['telemetry']:
        s=row['status']
        if s['time']==previous:continue
        previous=s['time']
        keys=('time','phase','secured','fault','door','latch','parcel','link','pending','delivered_ids','endpoint_ids','events','parcel_distances_m','door_angle_rad','latch_position_m','motion_peak_m_s2','grant','endpoint_duplicate_packets')
        rows.append({'at':row['video_time_s'],'status':{k:s[k] for k in keys}})
    (PUBLIC/f'{name}.json').write_text(json.dumps({'chapters':report['chapters'],'samples':rows,'checks':report['checks']},separators=(',',':')))
for name in ('webots_classification','webots_sensor_trials','webots_benchmark'):
    shutil.copy2(ROOT/'results'/f'{name}.json',PUBLIC/f'{name}.json')
print('Prepared verified footage and synchronized telemetry')
