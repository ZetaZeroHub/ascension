import {AbsoluteFill, Img, staticFile} from 'remotion';
export const Cover: React.FC = () => <AbsoluteFill style={{backgroundColor:'#101112'}}>
  <Img src={staticFile('frames/12-last.png')} style={{width:'100%',height:'100%',objectFit:'cover'}}/>
  <AbsoluteFill style={{background:'linear-gradient(0deg, rgba(0,0,0,0.65), transparent 45%)'}}/>
  <div style={{position:'absolute',left:112,bottom:86,color:'#f1e6d5',fontFamily:'"Microsoft YaHei",sans-serif'}}>
    <div style={{fontSize:86,fontWeight:300,letterSpacing:30}}>飞升</div>
    <div style={{fontSize:19,letterSpacing:5,marginTop:22}}>一场关于重力与光的旅程</div>
  </div>
</AbsoluteFill>;
