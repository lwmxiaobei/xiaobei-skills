import {Loop, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {VideoElementSpec} from '../types';
import {getEntrance} from './motion';

export const VideoElement: React.FC<{element: VideoElementSpec}> = ({element}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const entrance = getEntrance({frame, fps, entrance: element.enter, role: 'secondary'});
  const anchorX = element.anchorX ?? 0.5;
  const anchorY = element.anchorY ?? 0.5;

  const video = (
    <OffthreadVideo
      src={staticFile(element.src)}
      trimBefore={Math.max(0, Math.round((element.trimBeforeSeconds ?? 0) * fps))}
      trimAfter={
        element.trimAfterSeconds === undefined
          ? undefined
          : Math.max(1, Math.round(element.trimAfterSeconds * fps))
      }
      playbackRate={element.playbackRate ?? 1}
      volume={element.volume ?? 0}
      muted={element.muted ?? (element.volume ?? 0) === 0}
      style={{
        position: 'absolute',
        left: element.x,
        top: element.y,
        width: element.width,
        height: element.height,
        objectFit: element.fit ?? 'cover',
        objectPosition: element.objectPosition ?? 'center',
        zIndex: element.zIndex ?? 1,
        opacity: entrance.opacity * (element.opacity ?? 1),
        borderRadius: element.borderRadius ?? 0,
        transformOrigin: `${anchorX * 100}% ${anchorY * 100}%`,
        transform: `translate(${-anchorX * 100}%, ${-anchorY * 100}%) translate(${entrance.x}px, ${entrance.y}px) scale(${entrance.scale})`,
      }}
    />
  );

  if (element.loop && element.trimAfterSeconds !== undefined) {
    const sourceFrames = Math.max(
      1,
      Math.round(
        ((element.trimAfterSeconds - (element.trimBeforeSeconds ?? 0)) /
          (element.playbackRate ?? 1)) *
          fps,
      ),
    );
    return (
      <Loop durationInFrames={sourceFrames} layout="none">
        {video}
      </Loop>
    );
  }

  return video;
};
