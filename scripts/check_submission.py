"""Check a delivered project without Webots, Node.js, or document libraries."""
import argparse
import hashlib
import json
from pathlib import Path


REPORTS = (
    'logic_trials', 'robustness', 'webots_smoke', 'webots_development',
    'webots_sensor_trials', 'webots_classification', 'webots_benchmark',
    'webots_edge_cases', 'dashboard_validation', 'evaluation_manifest',
    'submission_validation', 'video_validation', 'render_validation',
    'workflow_recording', 'resilience_recording', 'portability_validation',
)
DOCUMENTS = (
    'README.md', 'SUBMISSION.md', 'DESIGN.md', 'REQUIREMENTS.md',
    'docs/FINAL_REPORT.md', 'docs/parcel_guard_report.tex', 'docs/SOFTWARE_REQUIREMENTS.md',
    'docs/PRESENTATION_GUIDE.md', 'docs/USER_GUIDE.md',
    'docs/proposal/Package Delivery Security Box - Written Proposal.pdf',
    'output/pdf/Parcel Guard - Final Report.pdf',
    'output/pdf/Parcel Guard - Final Presentation.pdf',
    'output/submission/Parcel Guard - Final Presentation.pptx',
)
VIDEOS = (
    'output/Parcel Guard - Final Demonstration.mp4',
    'output/Parcel Guard - Delivery Workflow.mp4',
    'output/Parcel Guard - Security Recovery.mp4',
)


def verify(root):
    root = Path(root).resolve()
    checks = []

    def file(relative):
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f'Path leaves the project: {relative}')
        if not path.is_file() or not path.stat().st_size:
            raise ValueError(f'Missing or empty file: {relative}')
        return path

    def digest(relative):
        return hashlib.sha256(file(relative).read_bytes()).hexdigest()

    def read(relative):
        return json.loads(file(relative).read_text())

    def hashes(entries):
        for relative, expected in entries.items():
            if digest(relative) != expected:
                raise ValueError(f'Content changed since validation: {relative}')

    reports = {}
    for name in REPORTS:
        reports[name] = read(f'results/{name}.json')
        if reports[name].get('passed') is not True:
            raise ValueError(f'Failed evidence: results/{name}.json')
    checks.append('All required saved reports passed')

    evaluation = reports['evaluation_manifest']
    hashes(evaluation['source_sha256'])
    hashes({f'results/{name}': value for name, value in evaluation['report_sha256'].items()})
    if reports['portability_validation'].get('source_sha256') != evaluation['source_sha256']:
        raise ValueError('Relocation test refers to a different runtime source')
    checks.append('Source and evaluation reports match their saved hashes')

    submission = reports['submission_validation']
    for name in DOCUMENTS:
        file(name)
        if name not in submission['artifact_sha256']:
            raise ValueError(f'Document has no validation hash: {name}')
    hashes(submission['artifact_sha256'])
    if digest('results/evaluation_manifest.json') != submission['evaluation_manifest_sha256']:
        raise ValueError('Submission documents refer to a different evaluation run')
    checks.append('Paper, presentation, guides, and submission checklist match validation')

    for mode in ('workflow', 'resilience'):
        if reports[f'{mode}_recording'].get('source_sha256') != evaluation['source_sha256']:
            raise ValueError(f'{mode} recording does not match the evaluated source')
        file(f'output/raw/{mode}.mp4')
    media = {item['path']: item for item in reports['render_validation']['videos']}
    for name in VIDEOS:
        item = media.get(name)
        if not item or item.get('passed') is not True or not item.get('all_frames_decoded_without_errors'):
            raise ValueError(f'Video has no successful full-frame validation: {name}')
        hashes({name: item['sha256']})
    checks.append('All three finished videos are validated; raw recordings are included')

    file('output/Package Delivery Security Box - Final Proposal.pptx')
    file('worlds/delivery_box.wbt')
    file('output/index.html')
    manifest_path = root / 'output/delivery_manifest.json'
    if manifest_path.exists():
        manifest = read('output/delivery_manifest.json')
        for item in manifest['files']:
            path = file(item['path'])
            if path.stat().st_size != item['bytes']:
                raise ValueError(f'Packaged file size changed: {item["path"]}')
            hashes({item['path']: item['sha256']})
        checks.append(f'All {len(manifest["files"])} packaged file hashes match')
    else:
        checks.append('No delivery manifest in this checkout; checked individual evidence hashes')
    return {'passed': True, 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f'Submission check failed: {error}')
        return 1
    for check in result['checks']:
        print(f'PASS {check}')
    print('Submission files verified. This checks saved evidence; it does not rerun the simulator.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
