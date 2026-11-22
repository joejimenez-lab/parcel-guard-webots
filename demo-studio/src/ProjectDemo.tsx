import { Video } from '@remotion/media';
import { AbsoluteFill, Sequence, staticFile, useCurrentFrame } from 'remotion';

const fps = 30;
const workflowStart = 0.4;
const workflowLength = 28;
const recoveryStart = 9.8;
const recoveryLength = 28.2;
export const projectDemoFrames = Math.round((workflowLength + recoveryLength) * fps);

const captions = {
  workflow: [
    [0, 'The courier enters the delivery code.'],
    [2.9, 'The bolt retracts and the door opens.'],
    [5.3, 'The courier places the package inside.'],
    [8.3, 'Delivery is recorded after the door closes and the bolt locks.'],
    [12.6, 'The used courier code is rejected.'],
    [16.1, 'The owner enters their code to collect the package.'],
    [20, 'The owner removes the package.'],
    [23.5, 'The empty box closes and locks again.'],
  ],
  resilience: [
    [0, 'Disconnect the message link.'],
    [12.3, 'Impact alerts stay queued while the link is offline.'],
    [18.5, 'Reconnect the link. The queued events are acknowledged.'],
    [20.7, 'Drop three acknowledgements to test message retries.'],
    [22.4, 'The receiver ignores duplicate messages.'],
    [24.5, 'The owner opens the box for a bolt fault test.'],
    [26.9, 'Block the bolt, then close the door.'],
    [31.6, 'The door is closed, but the bolt fault keeps the box unsecured.'],
    [35.1, 'Release the bolt. The box locks and the fault clears.'],
  ],
} satisfies Record<string, [number, string][]>;

const Recording: React.FC<{mode:'workflow'|'resilience'; start:number}> = ({mode,start}) => {
  const t=useCurrentFrame()/fps+start;
  const caption=captions[mode].findLast(([at])=>at<=t)?.[1];
  return <AbsoluteFill style={{background:'#f4f4f3',fontFamily:'Arial, sans-serif',color:'#1a1a1a'}}>
    <div style={{position:'absolute',left:32,top:22,fontSize:28}}>Webots simulation</div>
    <div style={{position:'absolute',left:1146,top:22,fontSize:28}}>Control panel</div>
    <Video src={staticFile(`project-demo/${mode}.mp4`)} trimBefore={Math.round(start*fps)} muted style={{position:'absolute',left:0,top:140,width:1136,height:639}} objectFit="contain" />
    <Video src={staticFile(`project-demo/${mode}-interface.mp4`)} trimBefore={Math.round(start*fps)} muted style={{position:'absolute',left:1140,top:66,width:760,height:855}} objectFit="contain" />
    <div style={{position:'absolute',left:32,top:814,width:1050,fontSize:32,color:'#444'}}>{mode==='workflow'?'Delivery and collection':'Message recovery and bolt fault'}</div>
    <div style={{position:'absolute',left:0,right:0,bottom:0,height:138,boxSizing:'border-box',background:'#fff',borderTop:'1px solid #bbb',display:'flex',alignItems:'center',padding:'20px 36px',fontSize:40,lineHeight:1.3}}>{caption}</div>
  </AbsoluteFill>;
};

export const ProjectDemo: React.FC = () => <>
  <Sequence durationInFrames={workflowLength*fps}><Recording mode="workflow" start={workflowStart}/></Sequence>
  <Sequence from={workflowLength*fps} durationInFrames={Math.round(recoveryLength*fps)}><Recording mode="resilience" start={recoveryStart}/></Sequence>
</>;
