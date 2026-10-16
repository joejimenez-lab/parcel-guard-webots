import {AbsoluteFill, Interactive, interpolate, useCurrentFrame} from 'remotion';
import {base,palette} from './style';
export const Opening:React.FC<{mode:'workflow'|'resilience'}>=({mode})=>{
 const frame=useCurrentFrame();
 return <AbsoluteFill style={base}>
  <div style={{position:'absolute',left:80,top:70,fontSize:26,letterSpacing:5,color:palette.mint}}>PARCEL GUARD</div>
  <Interactive.Div style={{position:'absolute',left:80,top:240,width:1300,opacity:interpolate(frame,[0,18],[0,1],{extrapolateRight:'clamp'})}}>
   <div style={{fontSize:82,fontWeight:700,lineHeight:1.1}}>{mode==='workflow'?'A delivery you can trust.':'When things go wrong.'}</div>
   <div style={{fontSize:36,lineHeight:1.4,color:palette.muted,marginTop:32,maxWidth:1120}}>{mode==='workflow'?'Courier access → parcel detection → confirmed locking → owner retrieval.':'Denied codes. Offline alerts. Lost acknowledgments. A blocked bolt and measured recovery.'}</div>
  </Interactive.Div>
  <div style={{position:'absolute',left:80,bottom:130,display:'flex',gap:24}}>{['Actual Webots footage','Live sensor telemetry','Reproducible Python'].map(text=><div key={text} style={{fontSize:24,border:'1px solid #46655b',padding:'16px 22px',borderRadius:9}}>{text}</div>)}</div>
  <div style={{position:'absolute',left:80,bottom:58,fontSize:22,color:palette.muted}}>Webots R2025a · Version 2.0 · One parcel at a time</div>
 </AbsoluteFill>
};
