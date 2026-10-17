import {Composition,Folder} from 'remotion';
import {FinalDemo} from './FinalDemo';
import {Workflow} from './Workflow';import {Resilience} from './Resilience';import {Opening} from './Opening';import {RecordedScene} from './RecordedScene';import {Evidence} from './Evidence';
export const RemotionRoot=()=> <>
 <Composition id="FinalDemonstration" component={FinalDemo} width={1920} height={1080} fps={30} durationInFrames={2822}/>
 <Composition id="DeliveryWorkflow" component={Workflow} width={1920} height={1080} fps={30} durationInFrames={1249}/>
 <Composition id="SecurityRecovery" component={Resilience} width={1920} height={1080} fps={30} durationInFrames={1633}/>
 <Folder name="Scenes">
  <Composition id="WorkflowOpening" component={Opening} defaultProps={{mode:'workflow' as const}} width={1920} height={1080} fps={30} durationInFrames={120}/>
  <Composition id="WorkflowRecording" component={RecordedScene} defaultProps={{mode:'workflow' as const}} width={1920} height={1080} fps={30} durationInFrames={949}/>
  <Composition id="WorkflowEvidence" component={Evidence} defaultProps={{mode:'workflow' as const}} width={1920} height={1080} fps={30} durationInFrames={180}/>
  <Composition id="SecurityOpening" component={Opening} defaultProps={{mode:'resilience' as const}} width={1920} height={1080} fps={30} durationInFrames={120}/>
  <Composition id="SecurityRecording" component={RecordedScene} defaultProps={{mode:'resilience' as const}} width={1920} height={1080} fps={30} durationInFrames={1333}/>
  <Composition id="SecurityEvidence" component={Evidence} defaultProps={{mode:'resilience' as const}} width={1920} height={1080} fps={30} durationInFrames={180}/>
 </Folder>
</>;
