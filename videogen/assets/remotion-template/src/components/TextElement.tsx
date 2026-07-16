import {useCurrentFrame, useVideoConfig} from 'remotion';
import type {TextElementSpec} from '../types';
import {getEntrance} from './motion';

export const TextElement: React.FC<{
  element: TextElementSpec;
  defaultFontFamily: string;
  defaultColor: string;
}> = ({element, defaultFontFamily, defaultColor}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const entrance = getEntrance({frame, fps, entrance: element.enter, role: 'secondary'});

  return (
    <div
      style={{
        position: 'absolute',
        left: element.x,
        top: element.y,
        width: element.width,
        zIndex: element.zIndex ?? 20,
        transform: `translate(-50%, -50%) translate(${entrance.x}px, ${entrance.y}px) scale(${entrance.scale})`,
        opacity: entrance.opacity * (element.opacity ?? 1),
        color: element.color ?? defaultColor,
        backgroundColor: element.backgroundColor ?? 'transparent',
        padding: element.padding ?? 0,
        borderRadius: element.borderRadius ?? 0,
        fontFamily: defaultFontFamily,
        fontSize: element.fontSize ?? 72,
        fontWeight: element.fontWeight ?? 700,
        lineHeight: element.lineHeight ?? 1.15,
        letterSpacing: element.letterSpacing ?? 0,
        textAlign: element.align ?? 'center',
        whiteSpace: 'pre-wrap',
        overflow: 'hidden',
        display: '-webkit-box',
        WebkitBoxOrient: 'vertical',
        WebkitLineClamp: element.maxLines ?? 4,
        textShadow: '0 3px 10px rgba(0,0,0,0.22)',
      }}
    >
      {element.text}
    </div>
  );
};
