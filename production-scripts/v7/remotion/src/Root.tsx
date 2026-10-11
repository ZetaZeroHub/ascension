import {AbsoluteFill, Composition, Sequence, staticFile, useCurrentFrame, interpolate} from 'remotion';
import {Video, Audio} from '@remotion/media';
import timeline from './timeline.json';

const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const ease=(x:number)=>1-Math.pow(1-clamp(x),3);
const hash=(i:number)=>{const x=Math.sin(i*127.1+311.7)*43758.5453;return x-Math.floor(x)};
const peaks=[57.6,67.2,74.4].map(t=>Math.round(t*24)/24);

// All motion is frame-derived and deterministic; no timers, CSS animations or random state.
const Atmosphere=({frame}:{frame:number})=>{
  const t=frame/24;
  const core=t-peaks[0], gravity=t-peaks[1], sky=t-peaks[2];
  const impact=peaks.reduce((a,p)=>a+(t>=p?Math.exp(-(t-p)*8):0),0);
  return <AbsoluteFill style={{pointerEvents:'none'}}>
    <svg viewBox="0 0 1280 720" width="1280" height="720" style={{position:'absolute',mixBlendMode:'screen'}}>
      <defs>
        <radialGradient id="seed-light"><stop stopColor="#f8dfab" stopOpacity=".45"/><stop offset="1" stopColor="#e4c38e" stopOpacity="0"/></radialGradient>
        <linearGradient id="sky-light" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#f2ecdc" stopOpacity=".32"/><stop offset="1" stopColor="#e2d7bf" stopOpacity="0"/></linearGradient>
        <mask id="seed-occlusion"><rect width="1280" height="720" fill="white"/><ellipse cx="662" cy="592" rx="69" ry="61" fill="black"/></mask>
        <filter id="soft-rays" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="28"/></filter>
      </defs>
      {core>=0&&core<2.4&&<g opacity={Math.pow(1-core/2.4,1.8)*.42} mask="url(#seed-occlusion)">
        <ellipse cx="662" cy="646" rx={45+ease(core/2.4)*950} ry={9+ease(core/2.4)*125} fill="none" stroke="#c9b58b" strokeWidth={2.1-core*.6}/>
        <ellipse cx="662" cy="646" rx={70+ease(core/2.4)*430} ry={15+ease(core/2.4)*65} fill="url(#seed-light)"/>
      </g>}
      {gravity>=0&&gravity<2.4&&Array.from({length:46},(_,i)=>{
        const d=gravity-hash(i+90)*.55;
        if(d<0)return null;
        const x=hash(i+1)*1280+Math.sin(d*2+i)*12;
        const y=650-hash(i+34)*170-d*d*(80+hash(i+3)*65);
        return <path key={i} d={`M${x},${y} l${hash(i+8)*3-1.5},${3+hash(i+12)*8}`} stroke="#d7c9a9" strokeWidth={.6+hash(i)*1.4} opacity={clamp(d*4)*clamp((2.4-gravity)*2)*(.13+hash(i+7)*.35)}/>;
      })}
      {sky>=0&&sky<2.4&&<g opacity={clamp(sky*7)*clamp((2.4-sky)*1.8)}>
        <path d={`M590 250 L690 250 L${1040+sky*50} 720 L${240-sky*50} 720 Z`} fill="url(#sky-light)" opacity=".25" filter="url(#soft-rays)"/>
        {Array.from({length:22},(_,i)=>{const d=sky-hash(i+4)*.18;if(d<0)return null;const angle=hash(i+7)*Math.PI*2;const r=90+d*(190+hash(i+5)*230);return <ellipse key={i} cx={640+Math.cos(angle)*r} cy={100+Math.sin(angle)*r*.7} rx={1+hash(i)*3} ry={.7+hash(i+3)*2} fill="#d6cfb9" opacity={clamp(1-d/1.5)*.35}/>})}
      </g>}
    </svg>
    <AbsoluteFill style={{backgroundColor:'#ded6bc',mixBlendMode:'screen',opacity:impact*.075}}/>
    <AbsoluteFill style={{background:'radial-gradient(ellipse at 50% 43%, transparent 42%, rgba(14,15,16,.2) 100%)'}}/>
  </AbsoluteFill>;
};

const Shot=({s}:{s:typeof timeline[number]})=>{
  const local=useCurrentFrame();
  const global=s.fromFrame+local;
  const t=global/24;
  const base=s.view==='eye'?1.15:s.view==='detail'?1.075:1;
  // Brief physical recoil at the first impact, then settle; no sustained handheld shake.
  const dt=t-peaks[0];
  const recoil=dt>=0&&dt<.6?Math.sin(dt*38)*Math.exp(-dt*9):0;
  const anticipation=s.source==='08'?Math.pow(clamp((s.trimBefore+local)/172),2)*.018:0;
  return <AbsoluteFill style={{overflow:'hidden'}}><Video src={staticFile(`graded/${s.source}.mp4`)} trimBefore={s.trimBefore} muted objectFit="cover" style={{width:'100%',height:'100%',transform:`translateY(${recoil*2}px) scale(${base+Math.abs(recoil)*.006+anticipation})`,transformOrigin:s.view==='eye'?'48% 37%':'50% 55%'}}/></AbsoluteFill>;
};

const Film=()=>{
  const frame=useCurrentFrame();
  const fade=interpolate(frame,[2246,2281],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  return <AbsoluteFill style={{backgroundColor:'#0a0b0b'}}>
    {timeline.map(s=><Sequence key={s.id} from={s.fromFrame} durationInFrames={s.duration}><Shot s={s}/></Sequence>)}
    <Atmosphere frame={frame}/>
    <Audio src={staticFile('audio/feisheng-master.wav')}/>
    {frame>=36&&frame<168&&<div style={{position:'absolute',left:64,bottom:48,fontSize:25,letterSpacing:12,color:'#e9e2d6',fontFamily:'Microsoft YaHei',opacity:interpolate(frame,[36,60,144,168],[0,1,1,0])}}>飞升</div>}
    <AbsoluteFill style={{backgroundColor:'#0a0b0b',opacity:fade}}/>
  </AbsoluteFill>;
};
export const Root=()=> <Composition id="FeishengV7" component={Film} width={1280} height={720} fps={24} durationInFrames={2282}/>;
