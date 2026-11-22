"""Verify current evaluated code and evidence without requiring Webots or Node."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lockbox.provenance import source_hashes

manifest = json.loads((ROOT/'results/evaluation_manifest.json').read_text())
errors = []
if not manifest['passed'] or source_hashes() != manifest['source_sha256']:
    errors.append('Evaluated source/configuration hashes do not match')
for name, digest in manifest['report_sha256'].items():
    path = ROOT/'results'/name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        errors.append(f'Report hash mismatch: {name}')
    elif not json.loads(path.read_text()).get('passed'):
        errors.append(f'Failing report: {name}')
if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
print(f"Verified {len(manifest['source_sha256'])} source/configuration files and {len(manifest['reports'])} passing evidence reports.")
