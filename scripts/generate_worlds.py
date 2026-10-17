"""One local, reproducible model generates every interactive/evaluation world."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
WORLDS = ROOT / 'worlds'
WORLDS.mkdir(exist_ok=True)
config = json.loads((ROOT / 'config/evaluation.json').read_text())

def block(position, size, color, metal=.0, rough=.65):
    xyz = ' '.join(map(str, position)); dimensions = ' '.join(map(str, size))
    return f'Transform {{ translation {xyz} children [ Shape {{ appearance PBRAppearance {{ baseColor {color} metalness {metal} roughness {rough} }} geometry Box {{ size {dimensions} }} }} ] }}'

panels = [((0,0,-.27),(.70,.64,.06)), ((-.33,0,0),(.04,.64,.56)), ((.33,0,0),(.04,.64,.56)), ((0,.30,0),(.70,.04,.56)), ((0,0,.28),(.70,.64,.04))]
body = '\n'.join(block(pos,size,'0.19 0.25 0.27',.45,.38) for pos,size in panels)
collisions = '\n'.join(f'Transform {{ translation {" ".join(map(str,p))} children [ Box {{ size {" ".join(map(str,s))} }} ] }}' for p,s in panels)
feet = '\n'.join(block((x,y,-.38),(.055,.055,.16),'0.09 0.12 0.13',.6) for x in (-.27,.27) for y in (-.25,.25))
sensors = '\n'.join(f'''DistanceSensor {{ translation {x} {y} .245 rotation 0 1 0 1.570796 name "parcel_{ix}_{iy}" type "generic" lookupTable [0 0 .005, .6 .6 .005] }}''' for ix,x in enumerate(config['sensor_coordinates_m']) for iy,y in enumerate(config['sensor_coordinates_m']))
keypad = '\n'.join(block((.22+(i%3)*.023,-.052,.02-(i//3)*.023),(.017,.008,.017),'0.71 0.79 0.78',.3,.35) for i in range(12))
pavers = '\n'.join(block((x,y,.044),(.49,.49,.025),'0.68 0.69 0.64') for x in (-1.5,-1,-.5,0,.5,1,1.5) for y in (-1.5,-1,-.5,0,.5,1,1.5))
wall_slats = '\n'.join(block((0,1.35,z),(4,.04,.008),'0.43 0.49 0.47') for z in (.15,.30,.45,.6,.75,.9,1.05,1.2,1.35,1.5))
planters = ''
for x in (-.9,.9):
    planters += block((x,.65,.16),(.32,.32,.32),'0.31 0.37 0.34')
    for dx,dy,z,r in ((0,0,.4,.18),(-.09,.02,.44,.12),(.06,-.06,.51,.14)):
        planters += f'Transform {{ translation {x+dx} {.65+dy} {z} children [ Shape {{ appearance PBRAppearance {{ baseColor .23 .38 .28 roughness 1 }} geometry Sphere {{ radius {r} subdivision 2 }} }} ] }}'
BASE = f'''#VRML_SIM R2025a utf8
WorldInfo {{ basicTimeStep 32 randomSeed 42 title "Parcel Guard | Delivery Security Box" info ["Version 2.2" "One parcel; local simulation and simulated connectivity"] }}
DEF CAMERA Viewpoint {{ orientation -0.186473 0.091566 0.978184 2.246021 position 1.7 -2.2 1.55 fieldOfView .62 }}
Background {{ skyColor [.40 .48 .48] }}
DirectionalLight {{ direction -.4 .5 -1 intensity 2 color 1 .96 .87 }}
DirectionalLight {{ direction .5 -.3 -.5 intensity .7 color .7 .86 1 }}
Solid {{ translation 0 0 -.04 children [ Shape {{ appearance PBRAppearance {{ baseColor .65 .68 .63 roughness 1 }} geometry Box {{ size 4 4 .08 }} }} {pavers} {wall_slats} {block((0,1.4,.80),(4,.1,1.6),'0.49 0.55 0.52')} {planters} ] boundingObject Box {{ size 4 4 .08 }} }}
DEF BOX Robot {{
 translation 0 0 .46 controller "lockbox_controller" window "lockbox_window"
 children [
  Emitter {{ name "status_tx" channel 2 }} Receiver {{ name "command_rx" channel 1 }}
  Emitter {{ name "scene_tx" channel 3 }} Emitter {{ name "event_tx" channel 4 }}
  {sensors}
  {body} {feet}
  {block((0,0,-.236),(.59,.55,.006),'0.46 0.53 0.51')}
  {block((0,-.315,.29),(.70,.028,.025),'0.39 0.83 0.71',.3,.3)}
  HingeJoint {{
   jointParameters HingeJointParameters {{ axis 0 0 -1 anchor -.35 -.32 0 minStop -0.02 maxStop 1.40 dampingConstant 0.1 }}
   device [ RotationalMotor {{ name "door_motor" minPosition 0 maxPosition 1.35 maxVelocity 1.5 maxTorque 20 }} PositionSensor {{ name "door_position" }} ]
   endPoint DEF DOOR Solid {{
    translation -.35 -.32 0
    children [
     Accelerometer {{ name "door_accel" translation .35 0 0 }}
     {block((.35,0,0),(.70,.035,.56),'0.14 0.38 0.37',.4,.32)}
     {block((.35,-.020,-.035),(.58,.008,.37),'0.17 0.44 0.42',.3,.38)}
     {block((.35,-.025,.16),(.34,.01,.038),'0.1 0.24 0.23',.2,.4)}
     LED {{ name "status_led" translation .35 -.033 .16 color [] gradual TRUE children [Shape {{ appearance PBRAppearance {{ baseColor 0 0 0 emissiveColor 0 0 0 roughness .4 }} geometry Box {{ size .28 .008 .013 }} }}] }}
     {block((.245,-.028,-.018),(.092,.025,.136),'0.08 0.12 0.13',.1,.6)}
     {keypad}
     {block((.59,-.047,0),(.038,.04,.15),'0.76 0.81 0.76',.8,.23)}
     {block((.10,-.024,.05),(.045,.01,.03),'0.39 0.83 0.71',.4,.3)}
     SliderJoint {{
      jointParameters JointParameters {{axis 1 0 0 position .08 minStop -.01 maxStop .09 dampingConstant 1}}
      device [ LinearMotor {{name "latch_motor" minPosition 0 maxPosition .08 maxVelocity .16 maxForce 50}} PositionSensor {{name "latch_position"}} Brake {{name "latch_brake"}} ]
      endPoint DEF BOLT Solid {{translation .59 -.045 0 children [Shape {{appearance PBRAppearance {{baseColor .93 .70 .30 metalness .7 roughness .25}} geometry Box {{size .12 .05 .045}}}}] name "bolt" boundingObject Box {{size .12 .05 .045}} physics Physics {{density -1 mass .1}}}}
     }}
    ]
    name "door" boundingObject Transform {{ translation .35 0 0 children [Box {{ size .70 .035 .56 }}] }} physics Physics {{density -1 mass 1}}
   }}
  }}
 ]
 name "Parcel Guard" boundingObject Group {{ children [{collisions}] }}
}}
DEF PARCEL Solid {{
 translation 1.05 -.35 .1
 children [
  Shape {{appearance PBRAppearance {{baseColor .65 .43 .23 roughness .85}} geometry Box {{size .28 .22 .20}}}}
  {block((0,0,.101),(.035,.222,.002),'0.84 0.72 0.49')}
  {block((0,-.111,0),(.035,.002,.2),'0.84 0.72 0.49')}
  {block((.07,-.113,.045),(.09,.002,.052),'0.94 0.93 0.84')}
 ]
 name "parcel" boundingObject Box {{size .28 .22 .20}}
}}
DEF FIXTURE Robot {{supervisor TRUE controller "scene_supervisor" children [Receiver {{name "scene_rx" channel 3}} Receiver {{name "event_rx" channel 4}} Emitter {{name "fixture_tx" channel 1}}] name "Independent scene fixture and simulated alert endpoint"}}
'''
RUNNER = '''DEF TEST_RUNNER Robot {supervisor TRUE controller "__CONTROLLER__" children [Emitter {name "command_tx" channel 1} Receiver {name "status_rx" channel 2}] name "Reproducible scenario runner"}
'''
(WORLDS/'delivery_box.wbt').write_text(BASE)
for suffix,controller in [('tests','trial_runner'),('edge_cases','edge_runner'),('sensor_trials','sensor_runner'),('classification','classification_runner'),('benchmark','cycle_runner'),('demo_video','demo_runner'),('resilience_video','resilience_demo')]:
    (WORLDS/f'delivery_box_{suffix}.wbt').write_text(BASE+RUNNER.replace('__CONTROLLER__',controller))
print('Generated 8 worlds from config/evaluation.json')
