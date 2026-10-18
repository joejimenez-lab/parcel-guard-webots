"""Native Webots recording plus synchronized sensor telemetry and assertions."""
import json
import math
import os
import time
from pathlib import Path
from .webots_harness import Harness, ROOT
from .provenance import source_hashes

def camera_pose(position, target):
    def unit(v):
        n=math.sqrt(sum(x*x for x in v)); return [x/n for x in v]
    def cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    x=unit([b-a for a,b in zip(position,target)])
    y=unit(cross([0,0,1],x)); z=cross(x,y)
    m=[[x[i],y[i],z[i]] for i in range(3)]
    angle=math.acos(max(-1,min(1,(m[0][0]+m[1][1]+m[2][2]-1)/2)))
    axis=unit([m[2][1]-m[1][2],m[0][2]-m[2][0],m[1][0]-m[0][1]])
    return [*axis,angle]


def record(name, frames, schedule, chapters, verify):
    h=Harness()
    video=ROOT/'output/raw'/f'{name}.mp4'
    video.parent.mkdir(exist_ok=True); video.unlink(missing_ok=True)
    cam=h.robot.getFromDef('CAMERA')
    cam.getField('position').setSFVec3f([1.3,-2.3,1.2])
    cam.getField('orientation').setSFRotation(camera_pose([1.3,-2.3,1.2],[.08,-.12,.40]))
    cam.getField('fieldOfView').setSFFloat(.76)
    telemetry=[]
    recording_started=None
    bridge = None
    if os.environ.get('PARCEL_GUARD_CAPTURE_UI') == '1':
        from .capture_bridge import CaptureBridge
        bridge = CaptureBridge(ROOT, name, frames, schedule)
    for frame in range(frames):
        done = bridge.before_step(h) if bridge else None
        h.step()
        if frame==8:
            # A moderate target avoids two-pass encoder failures in static scenes.
            h.robot.movieStartRecording(str(video),1920,1080,0,75,1,False)
            recording_started=h.robot.getTime()
        if not bridge and frame in schedule:
            action,data=schedule[frame]
            h.send(action,**data)
        if recording_started is not None and h.latest:
            telemetry.append({'video_time_s':round(h.robot.getTime()-recording_started,6),'status':h.latest})
        if bridge:
            bridge.after_step(h, done)
    h.robot.movieStopRecording()
    deadline=time.monotonic()+180
    while not h.robot.movieIsReady() and time.monotonic()<deadline:
        h.step()
    checks=verify(telemetry)
    checks['mp4_encoded']=video.exists() and video.stat().st_size>500000 and h.robot.movieIsReady() and not h.robot.movieFailed()
    report={'passed':all(checks.values()),'checks':checks,'frames':frames-8,'nominal_duration_s':(frames-8)*.032,
            'raw_video':str(video.relative_to(ROOT)),'source_sha256':source_hashes(),
            'interaction_source':'live browser form and button handlers' if bridge else 'scheduled commands',
            'interface_commands':bridge.received if bridge else [],
            'chapters':chapters,'telemetry':telemetry}
    (ROOT/'results'/f'{name}_recording.json').write_text(json.dumps(report,indent=2))
    print(name,json.dumps(checks),flush=True)
    if bridge:
        bridge.close()
    h.robot.simulationQuit(0 if report['passed'] else 1)
