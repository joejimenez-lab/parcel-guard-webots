import {Video} from '@remotion/media';
import {AbsoluteFill, staticFile, useCurrentFrame, useVideoConfig, delayRender, continueRender} from 'remotion';
import {useEffect,useState} from 'react';
import {base,palette} from './style';
type Status={time:number;phase:string;secured:boolean;fault:boolean;door:string;latch:string;parcel:string;link:string;pending:number;delivered_ids:number[];endpoint_ids:number[];events:{id:number;time:number;kind:string;detail:string}[];parcel_distances_m:number[];door_angle_rad:number;latch_position_m:number;motion_peak_m_s2:number;endpoint_duplicate_packets:number;grant:string};
type Data={chapters:{at:number;title:string;description:string}[];samples:{at:number;status:Status}[]};
const captions={
 workflow:[
 ['Ready for delivery','The empty box begins with the door closed and bolt extended.'],
 ['Courier access','A valid single-use code retracts the bolt before the door opens.'],
 ['Parcel detected','The distance array confirms a parcel; authorized placement records delivery.'],
 ['Closure confirmed','The controller closes the door, extends the bolt, and checks both positions.'],
 ['Used code rejected','The consumed courier code cannot open the box a second time.'],
 ['Owner access','The owner credential starts a separate, authorized retrieval session.'],
 ['Retrieval recorded','The parcel leaves the sensor array during the owner’s access window.'],
 ['Empty and secured','The box returns to a measured secure state, ready for the next session.']],
 resilience:[
 ['Failure tests','The following sequence injects access, connection, and actuator failures.'],
 ['Role mismatch rejected','A courier credential cannot be used as an owner credential.'],
 ['Expired code rejected','Expiry is checked locally, before any motor command is issued.'],
 ['Connection interrupted','Local sensing and control continue while notifications remain queued.'],
 ['Impacts recorded offline','Three spaced impacts generate distinct tamper events during the outage.'],
 ['Connection restored','Pending events are retried and acknowledged by their unique IDs.'],
 ['Lost acknowledgments','The sender retries; duplicate packets do not create duplicate receipts.'],
 ['Owner access granted','An authorized opening prepares the bolt for the obstruction test.'],
 ['Bolt blocked','The door closes, but the blocked bolt cannot reach its locking position.'],
 ['Measured fault','The timeout reports a bolt fault. The box does not report itself secured.'],
 ['Motion restored','Releasing the obstruction allows measured locking and clears the fault.']]
};
const pretty=(s:string)=>s.replaceAll('_',' ').toLowerCase().replace(/^./,x=>x.toUpperCase());
export const RecordedScene:React.FC<{mode:'workflow'|'resilience'}>=({mode})=>{
 const [handle]=useState(()=>delayRender('Recorded telemetry'));
 const [data,setData]=useState<Data|null>(null);
 useEffect(()=>{fetch(staticFile(`${mode}.json`)).then(r=>r.json()).then(d=>{setData(d);continueRender(handle)}).catch(e=>{throw e})},[mode,handle]);
 const frame=useCurrentFrame(),{fps}=useVideoConfig(),time=frame/fps;
 if(!data)return null;
 const s=(data.samples.findLast(r=>r.at<=time)||data.samples[0]).status;
 const chapter=data.chapters.findLast(c=>c.at<=time)||data.chapters[0];
 const n=data.chapters.indexOf(chapter);
 const [title,description]=captions[mode][Math.min(n,captions[mode].length-1)];
 const accent=s.fault?palette.red:s.secured?palette.mint:palette.amber;
 const recent=s.events.filter(e=>!['sensor_fault','sensor_recovered','boot'].includes(e.kind)).slice(-2);
 return <AbsoluteFill style={base}>
  <div style={{position:'absolute',left:64,top:35,fontSize:24,fontWeight:700,letterSpacing:2}}>PARCEL GUARD</div>
  <div style={{position:'absolute',right:64,top:35,fontSize:23,color:palette.muted}}>{mode==='workflow'?'01 / DELIVERY & RETRIEVAL':'02 / SECURITY & RECOVERY'}</div>
  <div style={{position:'absolute',left:64,right:64,top:83,height:1,background:'#c7ccc6'}}/>
  <div style={{position:'absolute',left:64,top:112,fontFamily:'Georgia, serif',fontSize:48}}>{title}</div>
  <div style={{position:'absolute',left:64,top:191,width:1392,height:783,overflow:'hidden',background:'#ced7d1'}}>
   <Video src={staticFile(`${mode}.mp4`)} muted style={{width:'100%',height:'100%'}} objectFit="contain"/>
   <div style={{position:'absolute',left:22,top:22,background:'#202828e8',color:'#fff',padding:'10px 16px',fontSize:21}}>WEBOTS RECORDING · {s.time.toFixed(1)} s simulated</div>
   <div style={{position:'absolute',left:0,right:0,bottom:0,padding:'23px 30px 26px',background:'#16201ff0',minHeight:112,color:'#fff',fontSize:30,lineHeight:1.4}}>{description}</div>
  </div>
  <aside style={{position:'absolute',left:1490,top:191,width:366,height:783}}>
   <div style={{fontSize:20,letterSpacing:2,color:palette.muted}}>MEASURED STATUS</div>
   <div style={{fontSize:36,fontWeight:700,color:accent,marginTop:12,marginBottom:26}}>{pretty(s.phase)}</div>
   {[['Door',`${s.door} · ${s.door_angle_rad.toFixed(2)} rad`],['Bolt',`${s.latch} · ${Math.round(s.latch_position_m*1000)} mm`],['Parcel',s.parcel],['Connection',s.link]].map(([label,value])=><div key={label} style={{borderTop:'1px solid #c7ccc6',padding:'13px 0'}}><div style={{fontSize:21,color:palette.muted}}>{label}</div><div style={{fontSize:27,marginTop:5}}>{pretty(value)}</div></div>)}
   <div style={{display:'flex',gap:28,borderTop:'1px solid #c7ccc6',paddingTop:18}}>{[[s.pending,'queued'],[s.endpoint_ids.length,'receipts'],[s.endpoint_duplicate_packets,'retries']].map(([value,label])=><div key={label}><div style={{fontSize:35,fontWeight:700,color:label==='queued'&&s.pending?palette.amber:palette.ink}}>{value}</div><div style={{fontSize:19,color:palette.muted,marginTop:3}}>{label}</div></div>)}</div>
   <div style={{marginTop:24,fontSize:18,letterSpacing:1,color:palette.muted}}>RECENT EVENTS</div>
   {recent.map(e=><div key={e.id} style={{fontSize:22,lineHeight:1.3,marginTop:13}}><span style={{color:palette.muted,fontSize:18}}>#{e.id} </span>{pretty(e.kind)}<div style={{fontSize:18,color:palette.muted,marginTop:3}}>{e.kind==='latch_fault'?'Target not reached within 2 s':e.detail}</div></div>)}
  </aside>
  <div style={{position:'absolute',left:64,bottom:35,fontSize:20,color:palette.muted}}>One parcel · local control · simulated message link</div>
  <div style={{position:'absolute',right:64,bottom:35,fontSize:20,color:palette.muted}}>{String(n+1).padStart(2,'0')} / {String(captions[mode].length).padStart(2,'0')}</div>
  <div style={{position:'absolute',left:64,right:64,bottom:15,height:3,background:'#d2d7d0'}}><div style={{height:'100%',width:`${Math.min(100,time/(mode==='workflow'?31.65:44.45)*100)}%`,background:palette.mint}}/></div>
 </AbsoluteFill>
};
