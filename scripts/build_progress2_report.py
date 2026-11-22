"""Build the canonical Progress Report 2 submission paper."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).with_name('build_progress2_submission_report.py')), run_name='__main__')
