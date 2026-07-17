import {Audio} from '@remotion/media';
import {AbsoluteFill, Series, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {PersistentFrame} from './components/PersistentFrame';
import {Scene} from './components/Scene';
import type {VideoSpec} from './types';

export const VideoComposition: React.FC<VideoSpec> = (props) => {
  const {fps} = useVideoConfig();
  const frame = useCurrentFrame();
  let cursor = 0;
  const activeScene = props.scenes.find((scene) => {
    const duration = Math.max(1, Math.round(scene.durationSeconds * fps));
    const active = frame >= cursor && frame < cursor + duration;
    cursor += duration;
    return active;
  });
  const musicVolume = activeScene?.voiceover
    ? props.audio?.musicDuckingVolume ?? 0.05
    : props.audio?.musicVolume ?? 0.12;

  return (
    <AbsoluteFill style={{backgroundColor: props.video.backgroundColor}}>
      {props.audio?.music ? (
        <Audio
          src={staticFile(props.audio.music)}
          volume={musicVolume}
          loop
        />
      ) : null}

      <Series>
        {props.scenes.map((scene) => (
          <Series.Sequence
            key={scene.id}
            durationInFrames={Math.max(1, Math.round(scene.durationSeconds * fps))}
            premountFor={fps}
          >
            <Scene scene={scene} theme={props.theme} />
          </Series.Sequence>
        ))}
      </Series>
      <PersistentFrame layout={props.layout} theme={props.theme} />
    </AbsoluteFill>
  );
};
