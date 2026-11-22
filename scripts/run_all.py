"""One command regenerates worlds and all required evidence, with frozen hashes."""
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lockbox.provenance import source_hashes
WEBOTS=os.environ.get('WEBOTS_BIN') or shutil.which('webots') or '/Applications/Webots.app/Contents/MacOS/webots'
REPORTS=[]

def hashes():
    return source_hashes()

def run(command,report,env=None):
    path=ROOT/'results'/report;path.unlink(missing_ok=True)
    r=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=180,env=env)
    (ROOT/'results'/f'{Path(report).stem}.log').write_text(r.stdout+'\n'+r.stderr)
    if r.returncode or not path.exists() or not json.loads(path.read_text()).get('passed'):
        print(r.stdout);print(r.stderr,file=sys.stderr)
        if path.exists(): print(json.dumps(json.loads(path.read_text()),indent=2)[:10000])
        raise SystemExit(f'Failed {report}')
    REPORTS.append(report)
    print(f'PASS {report}',flush=True)

def main():
    if not Path(WEBOTS).is_file():raise SystemExit('Set WEBOTS_BIN to the Webots executable')
    os.environ['PARCEL_GUARD_STATE_PATH']=''
    os.environ['PARCEL_GUARD_SECURE_MODE']='0'
    subprocess.run([sys.executable,'scripts/generate_worlds.py'],cwd=ROOT,check=True)
    frozen=hashes()
    run([sys.executable,'tests/run_trials.py'],'logic_trials.json')
    run([sys.executable,'tests/robustness.py'],'robustness.json')
    run([sys.executable,'tests/progress2.py'],'progress2_regressions.json')
    run([sys.executable,'tests/security_layers.py'],'security_layers.json')
    run(['node','tests/dashboard.cjs'],'dashboard_validation.json')
    options=[WEBOTS,'--batch','--no-rendering','--mode=fast','--stdout','--stderr']
    run(options+['worlds/delivery_box_tests.wbt'],'webots_smoke.json')
    run(options+['worlds/delivery_box_classification.wbt'],'webots_development.json',env={**os.environ,'EVAL_PHASE':'development'})
    run(options+['worlds/delivery_box_sensor_trials.wbt'],'webots_sensor_trials.json')
    run(options+['worlds/delivery_box_classification.wbt'],'webots_classification.json',env={**os.environ,'EVAL_PHASE':'final'})
    run(options+['worlds/delivery_box_benchmark.wbt'],'webots_benchmark.json')
    run(options+['worlds/delivery_box_edge_cases.wbt'],'webots_edge_cases.json')
    recovery_state=ROOT/'.runtime/evaluation-recovery.json'
    recovery_state.unlink(missing_ok=True)
    run(options+['worlds/delivery_box_progress2.wbt'],'webots_progress2.json',
        env={**os.environ,'PARCEL_GUARD_STATE_PATH':str(recovery_state)})
    security_state=ROOT/'.runtime/evaluation-security.json'
    security_state.unlink(missing_ok=True)
    run(options+['worlds/delivery_box_security.wbt'],'webots_security.json',
        env={**os.environ,'PARCEL_GUARD_STATE_PATH':str(security_state),
             'PARCEL_GUARD_SECURE_MODE':'1','PARCEL_GUARD_OWNER_PASSWORD':'evaluation-owner'})
    stable=frozen==hashes()
    manifest={'passed':stable,'timestamp_utc':datetime.now(timezone.utc).isoformat(),'webots':'R2025a',
              'python':sys.version.split()[0],'platform':platform.platform(),
              'configuration_unchanged_during_evaluation':stable,'source_sha256':frozen,'reports':REPORTS,
              'report_sha256':{p:hashlib.sha256((ROOT/'results'/p).read_bytes()).hexdigest() for p in REPORTS}}
    (ROOT/'results/evaluation_manifest.json').write_text(json.dumps(manifest,indent=2))
    if not stable:raise SystemExit('Source changed during evaluation; rerun before submission')
    subprocess.run([sys.executable,'scripts/build_report.py'],cwd=ROOT,check=True)
    print('All proposal targets and additional failure checks passed. Evidence: results/REPORT.md')
if __name__=='__main__':main()
