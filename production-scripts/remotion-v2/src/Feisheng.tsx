import {AbsoluteFill, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {Audio, Video} from '@remotion/media';
import {z} from 'zod';
import story from './data/storyboard.json';

export const mvSchema = z.object({showTitle: z.boolean()});
type Props = z.infer<typeof mvSchema>;
type Scene = (typeof story.scenes)[number];
const pushEnds: Record<string, number> = {'01':1.035, '02':1.035, '05':1.035, '07':1.07, '08':1.045, '09':1.1, '14':1.035};
const Shot: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const length = scene.to - scene.from;
  const push = interpolate(frame, [0, length - 1], [1, pushEnds[scene.id] ?? 1], {extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{overflow: 'hidden'}}>
    <Video src={staticFile(`graded/${scene.id}.mp4`)} muted objectFit="cover"
      style={{width: '100%', height: '100%', transform: `scale(${push})`}} />
  </AbsoluteFill>;
};
export const Feisheng: React.FC<Props> = ({showTitle}) => {
  const frame = useCurrentFrame();
  const titleOpacity = interpolate(frame, [36, 72, 144, 180], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const endFade = interpolate(frame, [2234, 2281], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{backgroundColor: '#080909'}}>
    {story.scenes.map(scene => <Sequence key={scene.id} name={`${scene.id} ${scene.title}`}
      from={scene.from} durationInFrames={scene.to - scene.from}>
      <Shot scene={scene}/>
    </Sequence>)}
    <Audio src={staticFile('audio/feisheng-master.wav')}/>
    {showTitle && <div style={{position: 'absolute', left: 104, bottom: 88, opacity: titleOpacity,
      color: '#eee9df', fontFamily: '"Microsoft YaHei", sans-serif', fontSize: 35,
      fontWeight: 300, letterSpacing: 18, textShadow: '0 2px 12px #0009'}}>飞升</div>}
    <AbsoluteFill style={{backgroundColor: '#080909', opacity: endFade}}/>
  </AbsoluteFill>;
};
