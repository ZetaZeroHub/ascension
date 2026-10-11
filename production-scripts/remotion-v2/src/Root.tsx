import {Composition} from 'remotion';
import {Feisheng, mvSchema} from './Feisheng';
import {Cover} from './Cover';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="Feisheng" component={Feisheng} schema={mvSchema}
        defaultProps={{showTitle: true}} durationInFrames={2282} fps={24} width={1920} height={1080}/>
      <Composition id="Cover" component={Cover} durationInFrames={1} fps={24} width={1920} height={1080}/>
    </>
  );
};
