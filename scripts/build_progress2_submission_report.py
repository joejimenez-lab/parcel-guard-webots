"""Compile the submission paper in the previously used IEEE report format."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(ROOT/'scripts/verify_progress2.py')],check=True)
def load(name):return json.loads((ROOT/'results'/f'{name}.json').read_text())
s=load('webots_sensor_trials');c=load('webots_classification');b=load('webots_benchmark')['checks']
security=load('webots_security');policy=load('security_layers');dashboard=load('dashboard_validation');recovery=load('progress2_regressions');m=load('evaluation_manifest')
values={'SecurityTests':policy['tests_run'],'DashboardChecks':len(dashboard['checks']),
        'SecurityGroups':len(security['checks']),'SecurityAssertions':sum(len(x) for x in security['checks'].values()),
        'RecoveryTests':recovery['tests_run'],'Presence':f"{s['correct']}/50",'MacroF':f"{c['macro_f1']:.2f}",
        'FalseAlarms':c['false_alarms'],'Cycles':b['motor_cycles']['successful'],
        'Recovered':b['connection_recovery']['recovered_events'],'Unauthorized':b['access_security']['unauthorized_unlocks'],
        'SourceCount':len(m['source_sha256']),'ReportCount':len(m['reports'])}
build=ROOT/'.build/progress2-submission/report';build.mkdir(parents=True,exist_ok=True)
(build/'progress2-evidence.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+str(v)+'}' for k,v in values.items())+'\n')
tex=os.environ.get('TEX_BIN') or shutil.which('pdflatex') or '/Library/TeX/texbin/pdflatex'
source=ROOT/'docs/parcel_guard_progress2_report.tex'
# Prefer this TeX distribution's packages over unrelated user-tree versions.
kpse=Path(tex).parent/'kpsewhich'
dist=subprocess.run([str(kpse),'-var-value=TEXMFDIST'],capture_output=True,text=True,check=True).stdout.strip()
env={**os.environ,'TEXINPUTS':str(build)+os.pathsep+dist+'/tex//'+os.pathsep+os.environ.get('TEXINPUTS','')}
for _ in range(3):
 run=subprocess.run([tex,'-interaction=nonstopmode','-halt-on-error','-output-directory',str(build),str(source)],cwd=ROOT,env=env,capture_output=True,text=True)
 if run.returncode:raise SystemExit((run.stdout+run.stderr)[-7000:])
log=(build/'parcel_guard_progress2_report.log').read_text()
problems=[line for line in log.splitlines() if any(x in line for x in ('Overfull \\hbox','Overfull \\vbox','undefined references','multiply-defined labels'))]
if problems:print('\n'.join(problems));raise SystemExit('Report requires layout/reference repair.')
output=ROOT/'output/pdf/Parcel Guard - Progress Report 2.pdf'
shutil.copy2(build/'parcel_guard_progress2_report.pdf',output)
print(output)
