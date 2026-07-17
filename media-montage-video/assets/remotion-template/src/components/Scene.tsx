import {Audio} from '@remotion/media';
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {SceneSpec, VideoSpec} from '../types';
import {Captions} from './Captions';
import {ImageElement} from './ImageElement';
import {TextElement} from './TextElement';
import {VideoElement} from './VideoElement';

export const Scene: React.FC<{
  scene: SceneSpec;
  theme: VideoSpec['theme'];
}> = ({scene, theme}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sceneDurationInFrames = Math.max(1, Math.round(scene.durationSeconds * fps));
  const cutPunch = interpolate(
    frame,
    [0, Math.max(1, Math.round(0.22 * fps))],
    [1.045, 1],
    {
      easing: Easing.out(Easing.cubic),
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    },
  );
  const backgroundScale = interpolate(
    frame,
    [0, Math.max(1, sceneDurationInFrames - 1)],
    [scene.background.startScale ?? 1, scene.background.endScale ?? 1.025],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const panDirection = scene.id.charCodeAt(scene.id.length - 1) % 2 === 0 ? 1 : -1;
  const backgroundPanX = interpolate(
    frame,
    [0, Math.max(1, sceneDurationInFrames - 1)],
    [-14 * panDirection, 14 * panDirection],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const elements = [...(scene.elements ?? [])].sort(
    (a, b) => (a.zIndex ?? 1) - (b.zIndex ?? 1),
  );

  return (
    <AbsoluteFill style={{backgroundColor: scene.background.color ?? '#16110f', overflow: 'hidden'}}>
      {scene.background.src ? (
        <Img
          src={staticFile(scene.background.src)}
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit: scene.background.fit ?? 'cover',
            transform: `translateX(${backgroundPanX}px) scale(${backgroundScale * cutPunch})`,
          }}
        />
      ) : null}

      {elements.map((element) =>
        element.type === 'image' ? (
          <ImageElement key={element.id} element={element} />
        ) : element.type === 'video' ? (
          <VideoElement key={element.id} element={element} />
        ) : (
          <TextElement
            key={element.id}
            element={element}
            defaultFontFamily={theme.fontFamily}
            defaultColor={theme.textColor}
          />
        ),
      )}

      {scene.voiceover ? <Audio src={staticFile(scene.voiceover)} /> : null}
      <Captions captions={scene.captions ?? []} theme={theme} />
    </AbsoluteFill>
  );
};
