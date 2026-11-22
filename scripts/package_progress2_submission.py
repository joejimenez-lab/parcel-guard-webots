"""Package the current written paper, slide backup and editable paper source."""
import hashlib
import json
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'output/progress-report-2'
files={str(p.relative_to(folder)):p.read_bytes() for p in folder.rglob('*') if p.is_file() and p.name!='MANIFEST.json'}
manifest={'sha256':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()}}
files['MANIFEST.json']=json.dumps(manifest,indent=2).encode()
(folder/'MANIFEST.json').write_bytes(files['MANIFEST.json'])
output=ROOT/'output/Parcel Guard - Progress Report 2 - Submission.zip'
with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for name,data in files.items():archive.writestr('Parcel Guard Progress Report 2 Submission/'+name,data)
with zipfile.ZipFile(output) as archive:
    assert archive.testzip() is None
    for name,digest in manifest['sha256'].items():
        assert hashlib.sha256(archive.read('Parcel Guard Progress Report 2 Submission/'+name)).hexdigest()==digest
print(f'{output} ({len(files)} files; hashes verified)')
