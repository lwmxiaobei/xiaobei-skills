import {Composition, type CalculateMetadataFunction} from 'remotion';
import config from '../video.json';
import {VideoComposition} from './Video';
import type {VideoSpec} from './types';

const video = config as VideoSpec;

const calculateMetadata: CalculateMetadataFunction<VideoSpec> = async ({props}) => {
  const durationInFrames = props.scenes.reduce(
    (total, scene) => total + Math.max(1, Math.round(scene.durationSeconds * props.video.fps)),
    0,
  );

  return {
    durationInFrames,
    width: props.video.width,
    height: props.video.height,
    fps: props.video.fps,
    defaultOutName: `${props.id}.mp4`,
  };
};

export const RemotionRoot = () => {
  const durationInFrames = video.scenes.reduce(
    (total, scene) => total + Math.max(1, Math.round(scene.durationSeconds * video.video.fps)),
    0,
  );

  return (
    <Composition
      id="MainVideo"
      component={VideoComposition}
      durationInFrames={durationInFrames}
      fps={video.video.fps}
      width={video.video.width}
      height={video.video.height}
      defaultProps={video}
      calculateMetadata={calculateMetadata}
    />
  );
};
