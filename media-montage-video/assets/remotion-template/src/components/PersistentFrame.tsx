import type {VideoSpec} from '../types';

export const PersistentFrame: React.FC<{
  layout: VideoSpec['layout'];
  theme: VideoSpec['theme'];
}> = ({layout, theme}) => {
  if (!layout || layout.preset !== 'tech-explainer') {
    return null;
  }

  return (
    <div style={{position: 'absolute', inset: 0, zIndex: 90, pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `linear-gradient(${layout.gridColor ?? 'rgba(50,255,120,0.08)'} 1px, transparent 1px), linear-gradient(90deg, ${layout.gridColor ?? 'rgba(50,255,120,0.08)'} 1px, transparent 1px)`,
          backgroundSize: '72px 72px',
          maskImage: 'linear-gradient(to bottom, black 0%, transparent 48%)',
        }}
      />
      {layout.brandLabel ? (
        <div
          style={{
            position: 'absolute',
            top: 44,
            left: 42,
            color: theme.textColor,
            fontFamily: theme.fontFamily,
            fontSize: 30,
            fontWeight: 700,
          }}
        >
          {layout.brandLabel}
        </div>
      ) : null}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 70,
          right: 70,
          textAlign: 'center',
          fontFamily: theme.fontFamily,
        }}
      >
        {layout.headline ? (
          <div style={{fontSize: 58, fontWeight: 850, color: theme.accentColor, lineHeight: 1.16}}>
            {layout.headline}
          </div>
        ) : null}
        {layout.subheadline ? (
          <div style={{marginTop: 18, fontSize: 34, fontWeight: 650, color: theme.textColor, lineHeight: 1.28}}>
            {layout.subheadline}
          </div>
        ) : null}
      </div>
    </div>
  );
};
