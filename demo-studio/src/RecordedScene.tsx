import {Video} from '@remotion/media';
import {AbsoluteFill, staticFile, useCurrentFrame, useVideoConfig, delayRender, continueRender} from 'remotion';
import {useEffect,useState} from 'react';
import {base,palette} from './style';
type Status={time:number;phase:string;secured:boolean;fault:boolean;door:string;latch:string;parcel:string;link:string;pending:number;delivered_ids:number[];endpoint_ids:number[];events:{id:number;time:number;kind:string;detail:string}[];parcel_distances_m:number[];door_angle_rad:number;latch_position_m:number;motion_peak_m_s2:number;endpoint_duplicate_packets:number;grant:string};
type Data={chapters:{at:number;title:string;description:string}[];samples:{at:number;status:Status}[]};
export const RecordedScene:React.FC<{mode:'workflow'|'resilience'}>=({mode})=>{
 const [handle]=useState(()=>delayRender('Recorded telemetry'));
 const [data,setData]=useState<Data|null>(null);
 useEffect(()=>{fetch(staticFile(`${mode}.json`)).then(r=>r.json()).then(d=>{setData(d);continueRender(handle)}).catch(e=>{throw e})},[mode,handle]);
 const frame=useCurrentFrame(),{fps}=useVideoConfig(),time=frame/fps;
 if(!data)return null;
 const row=data.samples.findLast(r=>r.at<=time)||data.samples[0];
 const s=row.status;
 const chapter=data.chapters.findLast(c=>c.at<=time)||data.chapters[0];
 const n=data.chapters.indexOf(chapter)+1;
 const accent=s.fault?palette.red:s.secured?palette.mint:palette.amber;
 return <AbsoluteFill style={base}>
  <div style={{position:'absolute',left:60,top:40,fontSize:24,color:palette.mint,letterSpacing:4,fontWeight:700}}>PARCEL GUARD</div>
  <div style={{position:'absolute',right:60,top:40,fontSize:21,color:palette.muted,letterSpacing:1}}>{mode==='workflow'?'01 / DELIVERY & RETRIEVAL':'02 / SECURITY & RECOVERY'} · WEBOTS</div>
  <div style={{position:'absolute',left:60,top:92,display:'flex',alignItems:'center',gap:22}}><span style={{fontSize:28,color:palette.mint,border:'1px solid #46655b',padding:'9px 15px',borderRadius:9}}>{String(n).padStart(2,'0')}</span><div style={{fontSize:48,fontWeight:650,letterSpacing:-1}}>{chapter.title}</div></div>
  <div style={{position:'absolute',left:60,top:178,width:1056,height:594,borderRadius:16,overflow:'hidden',border:'1px solid #486057'}}><Video src={staticFile(`${mode}.mp4`)} muted style={{width:'100%',height:'100%'}} objectFit="contain"/><div style={{position:'absolute',left:22,bottom:22,background:'#10221dde',padding:'10px 15px',fontSize:20,borderRadius:8,color:palette.ink}}>ACTUAL SIMULATION · {s.time.toFixed(1)} s</div></div>
  <aside style={{position:'absolute',left:1140,top:178,width:400,height:594,background:palette.panel,borderRadius:16,padding:26,border:'1px solid #334c47'}}>
   <div style={{fontSize:18,letterSpacing:3,color:palette.muted}}>MEASURED STATE</div><div style={{fontSize:35,fontWeight:700,color:accent,marginTop:9,marginBottom:18}}>{s.phase}</div>
   <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14}}>{[['Door',s.door],['Bolt',s.latch],['Parcel',s.parcel],['Link',s.link]].map(([label,value])=><div key={label} style={{padding:'10px 0',borderTop:'1px solid #40574f'}}><div style={{fontSize:18,color:palette.muted}}>{label}</div><div style={{fontSize:25,textTransform:'capitalize',marginTop:5,color:label==='Link'&&value==='offline'?palette.amber:palette.ink}}>{value}</div></div>)}</div>
   <div style={{fontSize:19,color:palette.muted,marginTop:17}}>DISTANCE ARRAY · METERS</div><div style={{display:'grid',gridTemplateColumns:'repeat(5,1fr)',gap:5,marginTop:10}}>{s.parcel_distances_m.map((v,i)=><div key={i} style={{background:v<.43?'#5ebe96':'#314b44',color:v<.43?'#10241a':'#c0d1c8',fontSize:17,textAlign:'center',padding:'5px 0',borderRadius:4}}>{v.toFixed(2)}</div>)}</div>
   <div style={{display:'flex',gap:20,marginTop:20}}><div><div style={{fontSize:36,color:s.pending?palette.amber:palette.mint,fontWeight:700}}>{s.pending}</div><div style={{fontSize:17,color:palette.muted}}>queued</div></div><div><div style={{fontSize:36,fontWeight:700}}>{s.endpoint_ids.length}</div><div style={{fontSize:17,color:palette.muted}}>unique receipts</div></div><div><div style={{fontSize:36,fontWeight:700}}>{Math.round(s.latch_position_m*1000)}</div><div style={{fontSize:17,color:palette.muted}}>bolt mm</div></div></div>
  </aside>
  <div style={{position:'absolute',left:60,top:800,maxWidth:1480,fontSize:26,lineHeight:1.3,color:palette.muted}}>{chapter.description}</div>
  <div style={{position:'absolute',left:60,right:60,bottom:0,height:4,background:'#2c453c'}}><div style={{height:'100%',width:`${Math.min(100,time/(mode==='workflow'?31.65:44.45)*100)}%`,background:palette.mint}}/></div>
 </AbsoluteFill>
};
