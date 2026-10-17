import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {base,palette} from './style';
export const Opening:React.FC<{mode:'workflow'|'resilience'|'final'}>=({mode})=>{
 const frame=useCurrentFrame();
 const title=mode==='final'?'Parcel Guard':mode==='workflow'?'Delivery and retrieval':'Security and recovery';
 const description=mode==='resilience'?'Denied access, retained alerts, lost acknowledgments, and a blocked bolt.':'A package delivery box with sensor-based events and measured locking.';
 return <AbsoluteFill style={base}>
  <div style={{position:'absolute',left:88,top:68,fontSize:24,letterSpacing:3,color:palette.muted}}>CS 5650 / WEBOTS R2025a</div>
  <div style={{position:'absolute',left:88,top:270,width:805,opacity:interpolate(frame,[0,15],[0,1],{extrapolateRight:'clamp'})}}>
   <div style={{fontFamily:'Georgia, serif',fontSize:mode==='final'?108:80,lineHeight:1.08,letterSpacing:-2}}>{title}</div>
   <div style={{fontSize:33,lineHeight:1.45,color:palette.muted,marginTop:36,width:730}}>{description}</div>
   <div style={{width:100,height:4,background:palette.mint,marginTop:42}}/>
   <div style={{fontSize:25,lineHeight:1.6,marginTop:28}}>Joshua Guico · Joe Jimenez · Brandon Lopez</div>
  </div>
  <div style={{position:'absolute',right:70,top:170,width:885,height:700,overflow:'hidden'}}><Img src={staticFile('cover.jpg')} style={{width:'100%',height:'100%',objectFit:'cover',objectPosition:'46% center'}}/></div>
  <div style={{position:'absolute',left:88,bottom:76,fontSize:24,color:palette.muted}}>Recorded simulation with synchronized telemetry · Version 2.2.0</div>
 </AbsoluteFill>
};
