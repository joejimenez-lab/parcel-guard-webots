"""Content hashes that bind saved evidence to the evaluated project."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source_hashes():
    paths = [ROOT / 'config/evaluation.json', ROOT / 'scripts/generate_worlds.py',
             ROOT / 'scripts/run_all.py', ROOT / 'scripts/build_report.py']
    for pattern in ('lockbox/*.py', 'controllers/*/*.py', 'tests/*.py',
                    'tests/*.cjs', 'worlds/*.wbt', 'plugins/robot_windows/lockbox_window/*'):
        paths.extend(ROOT.glob(pattern))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(paths)) if p.is_file()}
