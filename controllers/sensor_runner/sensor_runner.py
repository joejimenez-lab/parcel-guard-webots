"""50 balanced physical distance-array trials, including enclosure edges/noise."""
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lockbox.webots_harness import Harness
from lockbox.sensing import CONFIG
h = Harness()
parcel = h.robot.getFromDef('PARCEL')
position = parcel.getField('translation')
collision = parcel.getField('boundingObject').getSFNode().getField('size')
visual = parcel.getField('children').getMFNode(0).getField('geometry').getSFNode().getField('size')
rng = random.Random(CONFIG['final_seed']+1)
trials = []
error = None
try:
    h.advance(12)
    for i in range(50):
        present = i % 2 == 0
        size = [rng.uniform(.12,.29), rng.uniform(.12,.25), rng.uniform(.10,.24)]
        xlim, ylim = .30-size[0]/2, .26-size[1]/2
        center = [rng.uniform(-xlim,xlim), rng.uniform(-ylim,ylim), .22+size[2]/2]
        if i < 10 and present:
            center[0] = (-1 if i % 4 else 1)*xlim
        if not present:
            center = [rng.uniform(.8,1.3), rng.uniform(-.7,.3), size[2]/2]
        collision.setSFVec3f(size); visual.setSFVec3f(size); position.setSFVec3f(center)
        h.advance(15)
        trials.append({'trial':i,'expected':present,'detected':h.latest['parcel']=='present',
                       'size_m':size,'center_m':center,'distances_m':h.latest['parcel_distances_m']})
except Exception as e:
    error = str(e)
correct = sum(t['expected']==t['detected'] for t in trials)
fp = sum(not t['expected'] and t['detected'] for t in trials)
fn = sum(t['expected'] and not t['detected'] for t in trials)
h.finish({'passed':len(trials)==50 and correct>=48 and error is None, 'correct':correct,'trials':len(trials),
          'target':48,'occupied_trials':25,'empty_trials':25,'false_positives':fp,'false_negatives':fn,
          'sensitivity':(25-fn)/25,'specificity':(25-fp)/25,'seed':CONFIG['final_seed']+1,
          'sensor_noise_relative_std':.005,'timestep_ms':h.dt,'trial_details':trials,'runner_error':error},'webots_sensor_trials.json')
