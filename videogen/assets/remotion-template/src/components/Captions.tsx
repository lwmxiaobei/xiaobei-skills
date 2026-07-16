import {useCurrentFrame, useVideoConfig} from 'remotion';
import type {CaptionSpec, VideoSpec} from '../types';

export const Captions: React.FC<{
  captions: CaptionSpec[];
  theme: VideoSpec['theme'];
}> = ({captions, theme}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const time = frame / fps;
  const caption = captions.find((item) => time >= item.startSeconds && time < item.endSeconds);

  if (!caption) {
    return null;
  }

  const emphasis = caption.emphasis?.trim();
  const parts = emphasis ? caption.text.split(emphasis) : [caption.text];
  const fontSize = theme.captionFontSize ?? Math.round(Math.min(width, height) * 0.044);

  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        bottom: Math.round(height * 0.065),
        transform: 'translateX(-50%)',
        width: Math.round(width * 0.86),
        zIndex: 100,
        boxSizing: 'border-box',
        padding: `${Math.round(fontSize * 0.28)}px ${Math.round(fontSize * 0.48)}px`,
        borderRadius: Math.round(fontSize * 0.28),
        background: theme.captionBackground,
        color: theme.captionColor,
        fontFamily: theme.fontFamily,
        fontSize,
        fontWeight: 700,
        lineHeight: 1.28,
        textAlign: 'center',
        textShadow: '0 2px 5px rgba(0,0,0,0.55)',
      }}
    >
      {emphasis && parts.length > 1 ? (
        <>
          {parts[0]}
          <span style={{color: theme.accentColor}}>{emphasis}</span>
          {parts.slice(1).join(emphasis)}
        </>
      ) : (
        caption.text
      )}
    </div>
  );
};
