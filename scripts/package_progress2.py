"""Package the current local simulation and report without historical media."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT/'scripts/verify_progress2.py')], check=True)
files = set()
for folder in ('lockbox', 'controllers', 'worlds', 'plugins', 'config', 'scripts', 'tests'):
    files.update(p for p in (ROOT/folder).rglob('*')
                 if p.is_file() and not set(p.relative_to(ROOT).parts) & {'__pycache__', '.DS_Store'}
                 and p.suffix not in ('.pyc', '.log', '.wbproj'))
for name in ('README.md', 'DESIGN.md', 'REQUIREMENTS.md', 'SUBMISSION.md', 'THIRD_PARTY_NOTICES.md', '.gitignore',
             'docs/PROGRESS_REPORT_2.md', 'docs/PROGRESS_REPORT_2_DEMO.md', 'docs/USER_GUIDE.md',
             'docs/PROGRESS_REPORT_2_PRESENTATION_GUIDE.md', 'docs/parcel_guard_progress2_report.tex',
             'docs/assets/parcel-guard-workflow.png',
             'output/pdf/Parcel Guard - Progress Report 2 Slides.pdf',
             'docs/SOFTWARE_REQUIREMENTS.md', 'output/pdf/Parcel Guard - Progress Report 2.pdf',
             'results/REPORT.md', 'results/evaluation_manifest.json', 'results/progress2_layout.json'):
    files.add(ROOT/name)
manifest = json.loads((ROOT/'results/evaluation_manifest.json').read_text())
files.update(ROOT/'results'/name for name in manifest['reports'])
files.update((ROOT/'results').glob('*.csv'))
files.update(p for p in (ROOT/'results/progress1_baseline').glob('*') if p.is_file())
files.update((ROOT/'output/progress2').glob('security-*.png'))
for p in (ROOT/'demo-studio').rglob('*'):
    if (p.is_file() and not set(p.relative_to(ROOT/'demo-studio').parts)
            & {'node_modules', 'public', 'out', 'dist', '.remotion', '.cache', '.DS_Store'}):
        files.add(p)
start = '''PARCEL GUARD - PROGRESS REPORT 2

Open output/pdf/Parcel Guard - Progress Report 2.pdf for the current report.
Use docs/PROGRESS_REPORT_2_PRESENTATION_GUIDE.md and docs/PROGRESS_REPORT_2_DEMO.md
for the class rehearsal. The editable slides are saved in the chat viewer;
export them as PowerPoint there. A slide PDF viewing backup is included.
Open worlds/delivery_box.wbt in Webots R2025a for the interactive simulation.
The interactive world creates local saved state under .runtime/ on first run.
The interactive world defaults to password-only owner sign-in, managed access codes and lockdown.
Default local demo owner password: owner-5650 (unless configured at initialization).
Create an eight-digit courier or collection code through the verified owner console.
The fixed 2468/1357 codes work only in legacy fixture evaluation worlds.
Tampering revokes codes and enters persistent lockdown; reset cannot clear it.

VERIFY SAVED EVIDENCE (Python standard library only):
  python3 scripts/verify_progress2.py

REPEAT EVALUATION (Webots R2025a, Python 3.10+, Node.js):
  cd demo-studio
  npm ci
  cd ..
  python3 scripts/run_all.py

REBUILD REPORT (Python and TeX with IEEEtran installed):
  python3 scripts/build_progress2_report.py

This package contains code, current evidence, preserved baseline evidence,
the current report and recorded-status security screenshots. Historical
videos, editable final-paper/slide assets, raw media and installed dependencies
are excluded. Media-build commands in the historical README sections need
the original workspace's separate assets. No GitHub account is required.

PROGRESS2_PACKAGE_MANIFEST.json records the hashes of every included file
except the manifest itself. results/evaluation_manifest.json binds evaluated
runtime code to the current passing test reports. Receiver crash durability,
physical power interruption and general frozen-parcel diagnostics remain
outside the verified claims. No runtime state or access logs are bundled.
'''
payloads = {str(p.relative_to(ROOT)): p.read_bytes() for p in sorted(files)}
payloads['PROGRESS2_START_HERE.txt'] = start.encode()
hashes = {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}
payloads['PROGRESS2_PACKAGE_MANIFEST.json'] = json.dumps({'sha256': hashes}, indent=2).encode()
output = ROOT/'output/Parcel Guard - Progress Report 2 - Project.zip'
with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for name, data in payloads.items():
        archive.writestr('Parcel Guard Progress Report 2/'+name, data)
with zipfile.ZipFile(output) as archive:
    for name, digest in hashes.items():
        assert hashlib.sha256(archive.read('Parcel Guard Progress Report 2/'+name)).hexdigest() == digest
    assert archive.testzip() is None
print(f'{output} ({len(payloads)} files, {output.stat().st_size:,} bytes; hashes verified)')
