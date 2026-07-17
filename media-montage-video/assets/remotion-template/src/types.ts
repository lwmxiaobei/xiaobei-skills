export type EntranceType = 'none' | 'fade' | 'rise' | 'left' | 'right' | 'pop';
export type MotionRole = 'primary' | 'secondary' | 'tertiary' | 'static';

export type EntranceSpec = {
  type: EntranceType;
  atSeconds?: number;
  durationSeconds?: number;
  distance?: number;
};

export type DriftSpec = {
  x?: number;
  y?: number;
  scale?: number;
  periodSeconds?: number;
};

export type ElementBase = {
  id: string;
  x: number;
  y: number;
  width: number;
  zIndex?: number;
  opacity?: number;
  enter?: EntranceSpec;
};

export type ImageElementSpec = ElementBase & {
  type: 'image';
  src: string;
  height?: number;
  anchorX?: number;
  anchorY?: number;
  fit?: 'contain' | 'cover' | 'fill';
  role?: MotionRole;
  motionPreset?: 'drift' | 'character' | 'static';
  drift?: DriftSpec;
  style?: {
    filter?: string;
    borderRadius?: number;
  };
};

export type VideoElementSpec = ElementBase & {
  type: 'video';
  src: string;
  height: number;
  anchorX?: number;
  anchorY?: number;
  fit?: 'contain' | 'cover' | 'fill';
  objectPosition?: string;
  trimBeforeSeconds?: number;
  trimAfterSeconds?: number;
  playbackRate?: number;
  volume?: number;
  muted?: boolean;
  loop?: boolean;
  borderRadius?: number;
};

export type TextElementSpec = ElementBase & {
  type: 'text';
  text: string;
  fontSize?: number;
  fontWeight?: number;
  lineHeight?: number;
  letterSpacing?: number;
  align?: 'left' | 'center' | 'right';
  color?: string;
  backgroundColor?: string;
  padding?: number;
  borderRadius?: number;
  maxLines?: number;
};

export type ElementSpec = ImageElementSpec | VideoElementSpec | TextElementSpec;

export type CaptionSpec = {
  text: string;
  startSeconds: number;
  endSeconds: number;
  emphasis?: string;
};

export type SceneSpec = {
  id: string;
  durationSeconds: number;
  narrationText?: string;
  voiceover?: string;
  background: {
    color?: string;
    src?: string;
    fit?: 'contain' | 'cover' | 'fill';
    startScale?: number;
    endScale?: number;
  };
  elements?: ElementSpec[];
  captions?: CaptionSpec[];
};

export type VideoSpec = {
  schemaVersion: 1;
  id: string;
  title: string;
  description?: string;
  video: {
    width: number;
    height: number;
    fps: number;
    backgroundColor: string;
  };
  theme: {
    fontFamily: string;
    textColor: string;
    accentColor: string;
    captionColor: string;
    captionBackground: string;
    captionFontSize?: number;
    captionBottom?: number;
    captionMaxWidth?: number;
  };
  layout?: {
    preset?: 'full-frame' | 'tech-explainer';
    brandLabel?: string;
    headline?: string;
    subheadline?: string;
    contentTop?: number;
    contentHeight?: number;
    gridColor?: string;
  };
  audio?: {
    music?: string;
    musicVolume?: number;
    musicDuckingVolume?: number;
  };
  scenes: SceneSpec[];
};
