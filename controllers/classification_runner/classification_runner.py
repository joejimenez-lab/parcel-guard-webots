"""Separate development/final scenarios and an observed motion-only baseline."""
import os
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lockbox.webots_harness import Harness
from lockbox.sensing import CONFIG
h = Harness()
phase = os.environ.get('EVAL_PHASE','final')
seed = CONFIG['development_seed'] if phase == 'development' else CONFIG['final_seed']
rng = random.Random(seed)
parcel = h.robot.getFromDef('PARCEL')
position = parcel.getField('translation')
collision = parcel.getField('boundingObject').getSFNode().getField('size')
visual = parcel.getField('children').getMFNode(0).getField('geometry').getSFNode().getField('size')
classes = ('benign_motion','delivery','retrieval','tamper')
labels = [label for label in classes for _ in range(15)]
rng.shuffle(labels)
trials = []
error = None

def classify(kinds):
    return next((label for label in ('tamper','delivery','retrieval') if label in kinds),'benign_motion')

def metrics(field):
    matrix = {a:{b:sum(t['expected']==a and t[field]==b for t in trials) for b in classes} for a in classes}
    f1 = {}
    for c in classes:
        tp = matrix[c][c]
        fp = sum(matrix[o][c] for o in classes if o!=c)
        fn = sum(matrix[c][o] for o in classes if o!=c)
        f1[c] = 2*tp/(2*tp+fp+fn) if tp else 0
    return matrix, f1, sum(f1.values())/4

try:
    h.advance(15)
    idle = [max(abs(v) for v in s['door_accel_m_s2']) for s in h.trace]
    for i,label in enumerate(labels):
        size = [rng.uniform(.12,.29),rng.uniform(.12,.25),rng.uniform(.10,.24)]
        center = [rng.uniform(-(.30-size[0]/2),.30-size[0]/2),rng.uniform(-(.26-size[1]/2),.26-size[1]/2),.22+size[2]/2]
        collision.setSFVec3f(size); visual.setSFVec3f(size)
        outside = [1.05,-.35,size[2]/2]
        position.setSFVec3f(center if label=='retrieval' else outside)
        h.advance(15)
        h.reset()
        h.trace.clear()
        if label=='tamper':
            mode = 'forced_door' if i%2 else 'impact'
            h.send('force_open' if i%2 else 'impact')
            h.require(lambda s:'tamper' in s['event_kinds'],'Tamper stimulus was not detected')
            if i%2:
                h.require(lambda s:s['door_angle_rad']>=.35,'Forced door did not move')
                h.close()
            else:
                h.advance(32)
        else:
            mode = 'authorized_cycle'
            h.access('courier' if label=='delivery' else 'owner',f'{phase}-{i}')
            if label=='delivery': position.setSFVec3f(center)
            elif label=='retrieval': position.setSFVec3f(outside)
            elif i%3==0: h.send('impact',force=12)  # modest bump during approved handling
            h.advance(15)
            h.close()
        h.advance(12)
        kinds = h.latest['event_kinds']
        peak = max(s.get('motion_peak_m_s2',max(abs(v) for v in s['door_accel_m_s2'])) for s in h.trace)
        angles = [s['door_angle_rad'] for s in h.trace]
        angle_range = max(angles)-min(angles)
        baseline = 'tamper' if peak>CONFIG['motion_baseline_threshold_m_s2'] or angle_range>.05 else 'benign_motion'
        trials.append({'trial':i,'expected':label,'predicted':classify(kinds),'motion_only_prediction':baseline,
                       'motion_peak_m_s2':peak,'door_angle_range_rad':angle_range,'stimulus':mode,
                       'parcel_size_m':size,'parcel_center_m':center,'events':h.latest['all_events']})
except Exception as e:
    error = str(e)
matrix,f1,macro = metrics('predicted')
baseline_matrix,baseline_f1,baseline_macro = metrics('motion_only_prediction')
false_alarms = sum(t['expected']!='tamper' and t['predicted']=='tamper' for t in trials)
h.finish({'passed':len(trials)==60 and macro>=.9 and false_alarms<=2 and error is None,
          'phase':phase,'seed':seed,'timestep_ms':h.dt,'trials':len(trials),'per_class_count':15,
          'macro_f1':macro,'per_class_f1':f1,'confusion_matrix':matrix,'false_alarms':false_alarms,
          'non_tamper_trials':45,'false_alarm_rate':false_alarms/45,
          'motion_only_macro_f1':baseline_macro,'motion_only_confusion_matrix':baseline_matrix,
          'baseline_definition':'Observed acceleration peak >10.2 m/s² OR door angle range >0.05 rad, without access context',
          'idle_peak_m_s2':max(idle,default=0),'runner_error':error,'trial_details':trials},
          'webots_development.json' if phase=='development' else 'webots_classification.json')
