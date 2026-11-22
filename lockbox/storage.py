"""Atomic local checkpoints; the JSONL audit log is not the recovery database."""
import hashlib
import json
import os
from pathlib import Path
import tempfile


class StateError(ValueError):
    pass


class StateStore:
    def __init__(self, path):
        self.path = Path(path)
        self.last_state = None

    def load(self):
        if not self.path.exists():
            return None
        try:
            record = json.loads(self.path.read_text())
            payload = record['payload']
            canonical = json.dumps(payload, sort_keys=True, allow_nan=False)
            if record['sha256'] != hashlib.sha256(canonical.encode()).hexdigest():
                raise StateError('checkpoint checksum mismatch')
            if payload['version'] != 1:
                raise StateError('unsupported checkpoint version')
            self.last_state = json.loads(json.dumps(payload['state']))
            return payload
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise StateError('checkpoint unreadable or invalid') from exc

    def save(self, state, now):
        if state == self.last_state:
            return
        payload = {'version': 1, 'saved_at': now, 'state': state}
        canonical = json.dumps(payload, sort_keys=True, allow_nan=False)
        record = json.dumps({'payload': payload,
                             'sha256': hashlib.sha256(canonical.encode()).hexdigest()}, indent=2)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', dir=self.path.parent, delete=False) as stream:
                temporary = stream.name
                stream.write(record + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            directory = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            self.last_state = json.loads(json.dumps(state))
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
