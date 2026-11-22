"""Build the accompanying editable paper with a local TeX distribution."""
import os
from pathlib import Path
import shutil
import subprocess
ROOT=Path(__file__).resolve().parent
tex=shutil.which('pdflatex') or '/Library/TeX/texbin/pdflatex'
kpse=Path(tex).parent/'kpsewhich'
dist=subprocess.run([str(kpse),'-var-value=TEXMFDIST'],capture_output=True,text=True,check=True).stdout.strip()
env={**os.environ,'TEXINPUTS':str(ROOT)+os.pathsep+dist+'/tex//'+os.pathsep}
for _ in range(3):
 subprocess.run([tex,'-interaction=nonstopmode','-halt-on-error','parcel_guard_progress2_report.tex'],cwd=ROOT,env=env,check=True)
print(ROOT/'parcel_guard_progress2_report.pdf')
