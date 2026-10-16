import {AbsoluteFill,Interactive,interpolate,useCurrentFrame} from 'remotion';
import {base,palette} from './style';
export const Evidence:React.FC<{mode:'workflow'|'resilience'}>=({mode})=>{
 const frame=useCurrentFrame();
 const stats=mode==='workflow'?[['50 / 50','Parcel detection','25 empty + 25 occupied'],['1.00','Macro F1','60 balanced event sequences'],['100 / 100','Motor cycles','Measured door and bolt feedback']]:[['0 / 30','Unauthorized unlocks','6 cases per attack category'],['100 / 100','Outage alerts recovered','10 outages · unique IDs'],['2 / 2','Blocked bolt directions','Fault + measured recovery']];
 return <AbsoluteFill style={base}>
  <div style={{position:'absolute',left:80,top:70,fontSize:24,letterSpacing:4,color:palette.mint}}>PARCEL GUARD / VERIFIED IN WEBOTS</div>
  <div style={{position:'absolute',left:80,top:150,fontSize:68,fontWeight:700}}>{mode==='workflow'?'A complete, tested delivery cycle.':'Failures are visible. Recovery is measured.'}</div>
  <Interactive.Div style={{position:'absolute',left:80,right:80,top:315,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:22,opacity:interpolate(frame,[0,15],[0,1],{extrapolateRight:'clamp'})}}>{stats.map(([value,label,detail])=><div key={label} style={{background:palette.panel,padding:32,borderRadius:16,border:'1px solid #3a584d'}}><div style={{fontSize:64,fontWeight:700,color:palette.mint}}>{value}</div><div style={{fontSize:28,marginTop:20}}>{label}</div><div style={{fontSize:23,lineHeight:1.4,color:palette.muted,marginTop:12}}>{detail}</div></div>)}</Interactive.Div>
  <div style={{position:'absolute',left:80,right:80,top:675,fontSize:27,color:palette.muted,lineHeight:1.5}}>{mode==='workflow'?'0 false tamper alarms in 45 non-tamper sequences. Measured motion-only baseline: macro F1 0.10.':'Lost acknowledgments are retried and deduplicated. A blocked bolt never reports “secured”.'}</div>
  <div style={{position:'absolute',left:80,right:80,bottom:62,fontSize:21,color:palette.muted}}>Evidence: results/ · Fixed configuration: config/evaluation.json · Local simulation; simulated network; volatile queue.</div>
 </AbsoluteFill>
};
