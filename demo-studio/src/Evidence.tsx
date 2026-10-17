import {AbsoluteFill,staticFile,delayRender,continueRender} from 'remotion';
import {useEffect,useState} from 'react';
import {base,palette} from './style';
type Summary={presence:string;f1:string;falseAlarms:string;cycles:string;unauthorized:string;recovered:string;observer:string};
export const Evidence:React.FC<{mode:'workflow'|'resilience'|'final'}>=({mode})=>{
 const [handle]=useState(()=>delayRender('Evaluation summary'));
 const [s,setSummary]=useState<Summary|null>(null);
 useEffect(()=>{fetch(staticFile('summary.json')).then(r=>r.json()).then(d=>{setSummary(d);continueRender(handle)}).catch(e=>{throw e})},[handle]);
 if(!s)return null;
 const rows=mode==='workflow'?[[s.presence,'Presence decisions','25 empty + 25 occupied'],[s.f1,'Macro F1','60 balanced event sequences'],[s.cycles,'Complete motor cycles','Measured door and bolt endpoints']]:mode==='resilience'?[[s.unauthorized,'Unauthorized unlocks','Invalid, expired, reused, wrong role, replay'],[s.recovered,'Offline alerts recovered','10 outages; unique event IDs'],['2 / 2','Bolt fault directions','Blocked extension and retraction']]:[[s.presence,'Presence decisions'],[s.f1,'Macro F1 · 60 sequences'],[s.falseAlarms,'False tamper alarms'],[s.cycles,'Complete motor cycles'],[s.unauthorized,'Unauthorized unlocks'],[s.recovered,'Offline alerts recovered']];
 return <AbsoluteFill style={base}>
  <div style={{position:'absolute',left:88,top:68,fontSize:24,letterSpacing:3,color:palette.muted}}>PARCEL GUARD / EVALUATION</div>
  <div style={{position:'absolute',left:88,top:155,fontFamily:'Georgia, serif',fontSize:74}}>Results from the final test suite</div>
  <div style={{position:'absolute',left:88,right:88,top:330,display:'grid',gridTemplateColumns:mode==='final'?'1fr 1fr':'1fr',columnGap:100}}>{rows.map(([value,label,detail])=><div key={label} style={{borderTop:'1px solid #bfc8c1',padding:'27px 0',display:'flex',alignItems:'baseline',gap:40,minHeight:133}}><div style={{fontSize:53,fontWeight:700,color:palette.mint,width:252,flexShrink:0}}>{value}</div><div style={{fontSize:30}}>{label}{detail&&<div style={{fontSize:23,color:palette.muted,marginTop:8}}>{detail}</div>}</div></div>)}</div>
  <div style={{position:'absolute',left:88,right:88,bottom:135,fontSize:29,lineHeight:1.45,color:palette.muted}}>These results cover the generated Webots scenarios.<br/>Physical attack resistance, real networks, and restart persistence require further testing.</div>
  <div style={{position:'absolute',left:88,bottom:62,fontSize:23}}>Source, report, slides, and raw evidence: github.com/joejimenez-lab/parcel-guard-webots</div>
 </AbsoluteFill>
};
