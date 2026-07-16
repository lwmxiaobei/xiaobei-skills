import {Audio} from '@remotion/media';
import {AbsoluteFill, Series, staticFile, useVideoConfig} from 'remotion';
import {Scene} from './components/Scene';
import type {VideoSpec} from './types';

export const VideoComposition: React.FC<VideoSpec> = (props) => {
  const {fps} = useVideoConfig();

  return (
    <AbsoluteFill style={{backgroundColor: props.video.backgroundColor}}>
      {props.audio?.music ? (
        <Audio
          src={staticFile(props.audio.music)}
          volume={props.audio.musicVolume ?? 0.12}
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
    </AbsoluteFill>
  );
};
