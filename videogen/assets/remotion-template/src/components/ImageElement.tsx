import {Img, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ImageElementSpec} from '../types';
import {getEntrance} from './motion';

export const ImageElement: React.FC<{element: ImageElementSpec}> = ({element}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const entrance = getEntrance({frame, fps, entrance: element.enter, role: element.role});
  const period = Math.max(0.4, element.drift?.periodSeconds ?? 3.8) * fps;
  const phase = (frame / period) * Math.PI * 2;
  const driftX = (element.drift?.x ?? 0) * Math.sin(phase);
  const driftY = (element.drift?.y ?? 0) * Math.sin(phase * 0.83);
  const driftScale = 1 + (element.drift?.scale ?? 0) * Math.sin(phase * 0.67);
  const anchorX = element.anchorX ?? 0.5;
  const anchorY = element.anchorY ?? 0.5;
  const isCharacter = element.motionPreset === 'character';
  const isStatic = element.motionPreset === 'static';
  const breathPhase = (frame / fps / 3.1) * Math.PI * 2;
  const characterLift = isCharacter ? -5 * Math.sin(breathPhase) : 0;
  const characterSway = isCharacter ? 9 * Math.sin(breathPhase * 0.71) : 0;
  const characterLean = isCharacter ? 0.55 * Math.sin(breathPhase * 0.58) : 0;
  const characterTurn = isCharacter ? 0.8 * Math.sin(breathPhase * 0.43) : 0;
  const characterScaleX = isCharacter ? 1 + 0.004 * Math.sin(breathPhase) : 1;
  const characterScaleY = isCharacter ? 1 + 0.012 * Math.sin(breathPhase) : 1;
  const resolvedDriftX = isStatic ? 0 : driftX;
  const resolvedDriftY = isStatic ? 0 : driftY;
  const resolvedDriftScale = isStatic ? 1 : driftScale;

  return (
    <Img
      src={staticFile(element.src)}
      style={{
        position: 'absolute',
        left: element.x,
        top: element.y,
        width: element.width,
        height: element.height,
        objectFit: element.fit ?? 'contain',
        zIndex: element.zIndex ?? 1,
        opacity: entrance.opacity * (element.opacity ?? 1),
        borderRadius: element.style?.borderRadius,
        filter:
          element.style?.filter ??
          (isCharacter ? 'drop-shadow(0 28px 24px rgba(0,0,0,0.52))' : undefined),
        transformOrigin: `${anchorX * 100}% ${anchorY * 100}%`,
        transform: [
          `translate(${-anchorX * 100}%, ${-anchorY * 100}%)`,
          `translate(${entrance.x + resolvedDriftX + characterSway}px, ${
            entrance.y + resolvedDriftY + characterLift
          }px)`,
          isCharacter ? `perspective(1200px) rotateY(${characterTurn}deg)` : '',
          isCharacter ? `rotate(${characterLean}deg)` : '',
          `scale(${entrance.scale * resolvedDriftScale * characterScaleX}, ${
            entrance.scale * resolvedDriftScale * characterScaleY
          })`,
        ].join(' '),
      }}
    />
  );
};
