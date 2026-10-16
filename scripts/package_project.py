"""Create the portable submission only from passing reports and existing demos."""
import hashlib
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'output'
VIDEO_NAMES=('Parcel Guard - Delivery Workflow.mp4','Parcel Guard - Security Recovery.mp4')
def main():
    reports=('evaluation_manifest','webots_sensor_trials','webots_classification','webots_benchmark','robustness','video_validation','render_validation','workflow_recording','resilience_recording')
    for name in reports:
        p=ROOT/'results'/f'{name}.json'
        if not p.exists() or not json.loads(p.read_text()).get('passed'):raise SystemExit(f'Missing/failed {name}; run evaluation and video steps first')
    manifest=json.loads((ROOT/'results/evaluation_manifest.json').read_text())
    for name,sha in manifest['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise SystemExit(f'{name} changed after evaluation; rerun scripts/run_all.py')
    paths=[]
    for directory in ('lockbox','controllers','config','worlds','plugins','scripts','tests','results','demo-studio'):
        paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and not any(part in ('node_modules','.git','__pycache__','.remotion','.cache','build') for part in p.parts) and p.name not in ('.DS_Store','demo_video_validation.json','demo_video_status.json') and p.suffix != '.wbproj' and not (p.parent == ROOT/'demo-studio/public' and p.suffix == '.mp4'))
    paths.extend(ROOT/p for p in ('README.md','DESIGN.md','REQUIREMENTS.md','.gitignore','.gitattributes','THIRD_PARTY_NOTICES.md'))
    paths.extend(OUTPUT/p for p in (*VIDEO_NAMES,'Parcel Guard Preview.gif','index.html','Parcel Guard Workflow Poster.jpg','Parcel Guard Recovery Poster.jpg','Package Delivery Security Box - Final Proposal.pptx'))
    paths.extend((OUTPUT/'raw').glob('*.mp4'))
    paths=sorted(set(paths))
    for p in paths:
        if not p.is_file():raise SystemExit(f'Missing artifact {p}')
    delivery={'project':'Parcel Guard','version':'2.0','files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
    (OUTPUT/'delivery_manifest.json').write_text(json.dumps(delivery,indent=2))
    archive=OUTPUT/'Parcel Guard - Complete Project.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in paths:z.write(p,'Parcel Guard/'+str(p.relative_to(ROOT)))
        z.write(OUTPUT/'delivery_manifest.json','Parcel Guard/output/delivery_manifest.json')
    with zipfile.ZipFile(archive) as z:
        failure=z.testzip()
        if failure:raise SystemExit(f'ZIP integrity failure: {failure}')
    print(f'Created {archive.name}: {archive.stat().st_size/1e6:.1f} MB, {len(paths)+1} files, ZIP integrity checked')
if __name__=='__main__':main()
