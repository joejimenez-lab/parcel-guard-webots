import {AbsoluteFill,Series} from 'remotion';
import {Opening} from './Opening';
import {RecordedScene} from './RecordedScene';
import {Evidence} from './Evidence';
import {base,palette} from './style';
const Transition=()=> <AbsoluteFill style={base}><div style={{position:'absolute',left:88,top:300}}><div style={{fontSize:25,color:palette.muted,letterSpacing:3}}>PART 02</div><div style={{fontFamily:'Georgia, serif',fontSize:84,marginTop:32}}>Testing the failure paths</div><div style={{fontSize:34,color:palette.muted,marginTop:34}}>Access denials · message recovery · blocked bolt</div></div></AbsoluteFill>;
export const FinalDemo=()=> <Series>
 <Series.Sequence durationInFrames={150}><Opening mode="final"/></Series.Sequence>
 <Series.Sequence durationInFrames={949}><RecordedScene mode="workflow"/></Series.Sequence>
 <Series.Sequence durationInFrames={90}><Transition/></Series.Sequence>
 <Series.Sequence durationInFrames={1333}><RecordedScene mode="resilience"/></Series.Sequence>
 <Series.Sequence durationInFrames={300}><Evidence mode="final"/></Series.Sequence>
</Series>;
