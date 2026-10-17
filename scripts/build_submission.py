"""Refresh report evidence and compile the standalone LaTeX submission paper."""
import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/parcel_guard_report.tex'

def load(name):
    data = json.loads((ROOT / 'results' / f'{name}.json').read_text())
    if not data.get('passed'):
        raise SystemExit(f'Refusing to publish failed evidence: {name}')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-only', action='store_true', help='Refresh values without exporting a PDF')
    args = parser.parse_args()
    s, c, b = load('webots_sensor_trials'), load('webots_classification'), load('webots_benchmark')['checks']
    r = load('robustness')
    load('webots_edge_cases'); load('evaluation_manifest')
    values = {'Presence':f"{s['correct']}/50", 'MacroF':f"{c['macro_f1']:.2f}",
              'FalseAlarms':str(c['false_alarms']), 'Cycles':str(b['motor_cycles']['successful']),
              'LatencyCount':str(b['alert_latency']['within_1s']), 'Recovered':str(b['connection_recovery']['recovered_events']),
              'Unauthorized':str(b['access_security']['unauthorized_unlocks']), 'BaselineF':f"{c['motion_only_macro_f1']:.2f}",
              'ObserverDelay':f"{b['alert_latency']['max_stimulus_to_observer_s']:.3f}", 'Regressions':str(len(r['checks']))}
    text = SOURCE.read_text()
    for key, value in values.items():
        text, count = re.subn(r'\\newcommand\{\\'+key+r'\}\{[^}]*\}', lambda _: '\\newcommand{\\'+key+'}{'+value+'}', text)
        if count != 1: raise SystemExit(f'Missing or duplicate report macro: {key}')
    labels = ('benign_motion', 'delivery', 'retrieval', 'tamper')
    rows = []
    for label in labels:
        title = label.replace('_', ' ').capitalize()
        rows.append(title+' & '+' & '.join(str(c['confusion_matrix'][label][column]) for column in labels)+r'\\')
    text = re.sub(r'% BEGIN CONFUSION MATRIX.*?% END CONFUSION MATRIX', lambda _: '% BEGIN CONFUSION MATRIX\n'+'\n'.join(rows)+'\n% END CONFUSION MATRIX', text, flags=re.S)
    SOURCE.write_text(text)
    # A text companion remains useful in repository viewers. The typeset paper is canonical.
    mapping = dict(zip(('PRESENCE','F1','FALSE','CYCLES','LATENCY','RECOVERED','UNAUTHORIZED','BASELINE','OBSERVER','REGRESSIONS'), values.values()))
    for i, a in enumerate(labels):
        for j, z in enumerate(labels): mapping[f'CM{i}{j}'] = str(c['confusion_matrix'][a][z])
    companion = (ROOT/'docs/report_source.md').read_text()
    for k, v in mapping.items(): companion = companion.replace('@'+k+'@', v)
    if re.search(r'@[A-Z0-9]+@', companion): raise SystemExit('Unresolved text companion field')
    (ROOT/'docs/FINAL_REPORT.md').write_text(companion)
    if args.source_only:
        print('Refreshed LaTeX evidence values and text companion'); return
    tex = os.environ.get('TEX_BIN') or shutil.which('tectonic') or shutil.which('pdflatex')
    if not tex:
        for candidate in ('/Library/TeX/texbin/pdflatex',):
            if Path(candidate).is_file(): tex = candidate; break
    if not tex: raise SystemExit('Install Tectonic or a TeX distribution with pdflatex, or set TEX_BIN.')
    build = ROOT/'.build/report-latex'; build.mkdir(parents=True, exist_ok=True)
    if Path(tex).name == 'tectonic':
        commands = [[tex, '--keep-logs', '--keep-intermediates', '--outdir', str(build), str(SOURCE)]]
    else:
        commands = [[tex, '-interaction=nonstopmode', '-halt-on-error', '-output-directory', str(build), str(SOURCE)]] * 3
    for command in commands:
        p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if p.returncode: raise SystemExit((p.stdout+p.stderr)[-6000:])
    log = (build/'parcel_guard_report.log').read_text()
    forbidden = ('Overfull \\hbox', 'Overfull \\vbox', 'There were undefined references', 'There were multiply-defined labels')
    if any(message in log for message in forbidden): raise SystemExit('Report has layout or reference warnings; inspect .build/report-latex/parcel_guard_report.log')
    output = ROOT/'output/pdf/Parcel Guard - Final Report.pdf'; output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(build/'parcel_guard_report.pdf', output)
    print(f'Compiled {output.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)}')
if __name__ == '__main__': main()
