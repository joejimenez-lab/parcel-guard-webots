"""Deterministic policy. Decisions use measured sensors, never scene coordinates."""
from dataclasses import dataclass
import math
import uuid
from .config import CONFIG


@dataclass(frozen=True)
class Sensors:
    door_open: bool = False
    parcel_present: bool = False
    latch_locked: bool = True
    impact: bool = False
    latch_unlocked: bool | None = None
    door_closed: bool | None = None
    valid: bool = True

    @property
    def unlocked(self):
        return not self.latch_locked if self.latch_unlocked is None else self.latch_unlocked

    @property
    def closed(self):
        return not self.door_open if self.door_closed is None else self.door_closed


class Lockbox:
    def __init__(self, courier_code="2468", owner_code="1357", courier_valid_until=300.0,
                 owner_valid_until=86400.0, auto_ack=True, start_time=0.0):
        if not all(math.isfinite(v) and v >= 0 for v in (start_time, courier_valid_until, owner_valid_until)):
            raise ValueError("Token lifetimes and start time must be finite and nonnegative")
        self.courier_code, self.owner_code = courier_code, owner_code
        self.courier_valid_until = start_time + courier_valid_until
        self.owner_valid_until = start_time + owner_valid_until
        self.session = uuid.uuid4().hex[:12]
        self.auto_ack = auto_ack
        self.courier_used = False
        self.failure_times, self.seen_request_ids = [], set()
        self.locked_until = 0.0
        self.grant, self.grant_until = None, 0.0
        self.door_was_open = False
        self.latch_target = 1.0
        self.link_online = True
        self.pending, self.delivered, self.history = [], [], []
        self.next_id = 1
        self.previous = Sensors()
        self.last_impact_at = -100.0
        self.authorized_motion_until = 0.0
        self.target_since = start_time
        self.fault_reported = False
        self.sensor_fault = False
        self.closing_since = None
        self.door_fault = False
        self.has_feedback = False

    def _target(self, locked, now):
        if self.latch_target != float(locked):
            self.latch_target = float(locked)
            self.target_since = now

    def request_close(self, now):
        """End authorization immediately; retract the bolt until the door closes."""
        had_grant = self.grant is not None
        self.grant = None
        if self.closing_since is None and (had_grant or not self.previous.closed or not self.latch_target):
            self.closing_since = now

    def _event(self, kind, now, detail="", detected_at=None):
        event = {"session": self.session, "id": self.next_id, "time": round(now, 6),
                 "kind": kind, "detail": detail}
        if detected_at is not None:
            event["sensor_time"] = round(detected_at, 6)
            event["queue_latency_s"] = round(now - detected_at, 6)
        self.next_id += 1
        self.history.append(event)
        self.pending.append(event)
        self._flush()
        return event

    def _flush(self):
        if self.auto_ack and self.link_online:
            for event in list(self.pending):
                self.acknowledge(self.session, event["id"])

    def acknowledge(self, session, event_id):
        if session != self.session or not self.link_online:
            return False
        for event in self.pending:
            if event["id"] == event_id:
                self.pending.remove(event)
                self.delivered.append(event)
                return True
        return False

    def set_link(self, online, now):
        if self.link_online != online:
            self.link_online = online
            self._event("link_restored" if online else "link_lost", now)
        self._flush()

    def request_access(self, code, now, sensors, request_id, intent=None):
        if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 128:
            self._event("access_denied", now, "missing or malformed request ID")
            return False
        if request_id in self.seen_request_ids:
            self._event("access_denied", now, "replayed request ID")
            return False
        self.seen_request_ids.add(request_id)
        if now < self.locked_until:
            self._event("access_denied", now, "code entry paused")
            return False
        reason, role = "invalid code", None
        if code == self.owner_code:
            role, reason = "owner", "expired owner code"
            if now >= self.owner_valid_until:
                role = None
        elif code == self.courier_code:
            role, reason = "courier", "expired courier code"
            if now >= self.courier_valid_until:
                role = None
            elif self.courier_used:
                role, reason = None, "courier code already used"
        if role and intent is not None and intent != role:
            role, reason = None, "code does not match requested role"
        if role == "courier" and sensors.parcel_present:
            role, reason = None, "box occupied"
        if role is None:
            self.failure_times = [t for t in self.failure_times if now - t <= CONFIG["code_failure_window_s"]]
            self.failure_times.append(now)
            self._event("access_denied", now, reason)
            if len(self.failure_times) >= CONFIG["code_failure_limit"]:
                self.locked_until = now + CONFIG["code_cooldown_s"]
                self.failure_times.clear()
                self._event("entry_paused", now, "60 seconds")
            return False
        if (self.grant or self.closing_since is not None or not sensors.valid or not sensors.closed
                or not sensors.latch_locked or self.fault_reported or self.door_fault):
            self._event("access_denied", now, "door, latch, or sensor not secure")
            return False
        self.failure_times.clear()
        self.previous = sensors
        self.has_feedback = True
        self.grant, self.grant_until = role, now + CONFIG["access_window_s"]
        self.door_was_open = False
        self.latch_target, self.target_since = 0.0, now
        if role == "courier":
            self.courier_used = True
        self._event("access_granted", now, role)
        return True

    def tick(self, now, sensors):
        previous = self.previous
        if self.grant and now >= self.grant_until:
            self._event("access_expired", now, "access window ended; closing door")
            self.request_close(now)
        if not sensors.valid and not self.sensor_fault:
            self._event("sensor_fault", now, "device feedback unavailable or not yet stable")
            if self.grant:
                self.request_close(now)
        elif sensors.valid and self.sensor_fault:
            self._event("sensor_recovered", now, "stable device feedback restored")
        self.sensor_fault = not sensors.valid
        if not sensors.valid:
            # Preserve the last valid sample across a gap. Invalid feedback must
            # neither invent a door edge nor silently renew authorization.
            return
        if sensors.door_open and not previous.door_open and self.grant is None:
            self._event("tamper", now, "door opened without approval", now)
        closing_motion = self.closing_since is not None and now - self.closing_since < CONFIG["door_close_timeout_s"]
        if (sensors.impact and self.grant is None and not closing_motion and now >= self.authorized_motion_until
                and now - self.last_impact_at >= CONFIG["impact_refractory_s"]):
            self.last_impact_at = now
            self._event("tamper", now, "impact detected", now)
        if self.has_feedback and sensors.parcel_present != previous.parcel_present:
            access_open = sensors.door_open or previous.door_open
            if self.grant == "courier" and sensors.parcel_present and access_open:
                self._event("delivery", now, "parcel placed", now)
            elif self.grant == "owner" and not sensors.parcel_present and access_open:
                self._event("retrieval", now, "parcel removed", now)
            else:
                self._event("tamper", now, "unapproved parcel movement", now)
        if self.grant and sensors.door_open:
            self.door_was_open = True
        if self.grant and sensors.closed and (self.door_was_open or now >= self.grant_until):
            self.request_close(now)
        if self.closing_since is not None and sensors.closed:
            if self.door_fault:
                self._event("door_recovered", now, "measured door reached closed position")
            self.door_fault = False
            self.closing_since = None
            self.authorized_motion_until = now + CONFIG["post_close_motion_grace_s"]
            self._target(True, now)
        elif self.closing_since is not None:
            self._target(False, now)
            if not self.door_fault and now - self.closing_since >= CONFIG["door_close_timeout_s"]:
                self._event("door_fault", now, "door did not close within the allowed time")
                self.door_fault = True
        reached = sensors.valid and (sensors.latch_locked if self.latch_target else sensors.unlocked)
        if not self.fault_reported and now - self.target_since >= CONFIG["latch_timeout_s"] and not reached:
            self._event("latch_fault", now, "measured bolt did not reach target within 2 seconds")
            self.fault_reported = True
        elif self.fault_reported and reached:
            self._event("latch_recovered", now, "measured bolt reached target")
            self.fault_reported = False
        self.previous = sensors
        self.has_feedback = True

    def status(self, now, sensors):
        fault = self.fault_reported or self.door_fault or not sensors.valid
        secure = sensors.valid and sensors.closed and sensors.latch_locked and not fault and not self.grant and self.closing_since is None
        if fault:
            phase = "FAULT"
        elif self.closing_since is not None:
            phase = "CLOSING"
        elif self.grant:
            phase = "UNLOCKING" if not sensors.unlocked else ("ACCESS" if sensors.door_open else "OPENING")
            if now >= self.grant_until:
                phase = "CLOSING"
        elif not sensors.closed:
            phase = "UNSECURED"
        else:
            phase = "SECURED" if secure else "LOCKING"
        return {"session": self.session, "time": round(now, 3), "phase": phase,
                "secured": secure, "fault": fault,
                "fault_reason": "sensor" if not sensors.valid else ("door" if self.door_fault else ("bolt" if self.fault_reported else None)),
                "door": "open" if sensors.door_open else ("closed" if sensors.closed else "moving"),
                "latch": "locked" if sensors.latch_locked else ("unlocked" if sensors.unlocked else "moving"),
                "parcel": "present" if sensors.parcel_present else "empty",
                "link": "online" if self.link_online else "offline", "grant": self.grant or "none",
                "entry_paused_s": max(0, round(self.locked_until - now, 1)),
                "access_remaining_s": max(0, round(self.grant_until - now, 1)) if self.grant else 0,
                "courier_code_used": self.courier_used, "pending": len(self.pending),
                "events": self.history[-16:]}
