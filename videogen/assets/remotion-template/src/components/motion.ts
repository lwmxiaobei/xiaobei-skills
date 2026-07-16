import {interpolate, spring} from 'remotion';
import type {EntranceSpec, MotionRole} from '../types';

const roleDefaults: Record<MotionRole, {distance: number; duration: number; scale: number}> = {
  primary: {distance: 90, duration: 0.8, scale: 0.86},
  secondary: {distance: 64, duration: 0.7, scale: 0.9},
  tertiary: {distance: 38, duration: 0.6, scale: 0.95},
  static: {distance: 0, duration: 0.01, scale: 1},
};

export const getEntrance = ({
  frame,
  fps,
  entrance,
  role = 'secondary',
}: {
  frame: number;
  fps: number;
  entrance?: EntranceSpec;
  role?: MotionRole;
}) => {
  const fallback = roleDefaults[role];
  const type = entrance?.type ?? (role === 'static' ? 'none' : 'fade');
  const startFrame = Math.round((entrance?.atSeconds ?? 0) * fps);
  const durationInFrames = Math.max(1, Math.round((entrance?.durationSeconds ?? fallback.duration) * fps));
  const distance = entrance?.distance ?? fallback.distance;
  const activeFrame = Math.max(0, frame - startFrame);
  const springProgress = spring({
    frame: activeFrame,
    fps,
    durationInFrames,
    config: {damping: 200},
  });
  const linearProgress = interpolate(activeFrame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const visible = frame >= startFrame;

  if (type === 'none') {
    return {opacity: 1, x: 0, y: 0, scale: 1};
  }

  return {
    opacity: visible ? (type === 'fade' ? linearProgress : springProgress) : 0,
    x:
      type === 'left'
        ? interpolate(springProgress, [0, 1], [-distance, 0])
        : type === 'right'
          ? interpolate(springProgress, [0, 1], [distance, 0])
          : 0,
    y: type === 'rise' ? interpolate(springProgress, [0, 1], [distance, 0]) : 0,
    scale:
      type === 'pop'
        ? interpolate(springProgress, [0, 1], [fallback.scale, 1])
        : 1,
  };
};
