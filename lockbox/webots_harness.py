"""Reusable scenario-driver helpers. Only imported by Supervisor controllers."""
import json
from pathlib import Path
from controller import Supervisor
ROOT = Path(__file__).resolve().parents[1]

class Harness:
    def __init__(self):
        self.robot = Supervisor()
        self.dt = int(self.robot.getBasicTimeStep())
        self.tx = self.robot.getDevice('command_tx')
        self.rx = self.robot.getDevice('status_rx')
        self.rx.enable(self.dt)
        self.latest = None
        self.observed = {}
        self.trace = []

    def step(self):
        if self.robot.step(self.dt) == -1:
            raise RuntimeError('Simulator stopped before the scenario completed')
        while self.rx.getQueueLength():
            self.latest = json.loads(self.rx.getString())
            self.trace.append(self.latest)
            for e in self.latest['events']:
                self.observed.setdefault((e['session'], e['id']), (e, self.robot.getTime()))
            self.rx.nextPacket()

    def advance(self, count):
        for _ in range(count):
            self.step()

    def send(self, action, **data):
        self.tx.send(json.dumps({'action': action, **data}).encode())

    def wait(self, predicate, limit=200):
        for _ in range(limit):
            self.step()
            if self.latest and predicate(self.latest):
                return True
        return False

    def require(self, predicate, message, limit=200):
        if not self.wait(predicate, limit):
            state = {k: self.latest.get(k) for k in ('phase', 'door_angle_rad', 'latch_position_m', 'fault_reason', 'grant', 'secured')} if self.latest else None
            raise RuntimeError(f'{message}; final measured state: {state}')

    def reset(self, **data):
        previous_session = self.latest['session'] if self.latest else None
        self.send('reset_logic', **data)
        self.require(lambda s: s['session'] != previous_session, 'Policy reset did not arrive')
        self.require(lambda s: s['secured'], 'Reset did not settle to secured')
        self.advance(5)

    def access(self, role, request_id):
        self.send('access', role=role, code='2468' if role == 'courier' else '1357', request_id=request_id)
        self.require(lambda s: s['door_angle_rad'] >= 1 and s['latch'] == 'unlocked', 'Approved access did not open fully')

    def close(self):
        self.send('close')
        self.require(lambda s: s['secured'], 'Door/bolt did not return to secured')
        self.advance(5)

    def finish(self, report, filename):
        (ROOT/'results'/filename).write_text(json.dumps(report, indent=2))
        print(filename, json.dumps({k:v for k,v in report.items() if k in ('passed','runner_error','macro_f1','correct','checks')}), flush=True)
        self.robot.simulationQuit(0 if report['passed'] else 1)
