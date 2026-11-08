# Ancient CCTV Video

Make a silent ancient Chinese story video in fake surveillance camera style.

Fixed high-angle camera, black and white footage, running timestamp and CAM label, no narration. Story is told by people moving in frame and by jumps in the timestamp.

## What it makes

- 30 to 40 seconds, 1280x720, 24fps, silent
- 3 to 4 segments of 10 seconds each, chained clip by clip from the previous clip's last frame
- Top bar with date and running timecode, REC top right, CAM label bottom left

## Examples already made with this skill

- Pan Jinlian, the original reference, CAM1 阳谷县紫石街电杆
- Wu Song fights the tiger, CAM2 景阳冈山道, 31.5 seconds
- Sima Guang smashes the vat, CAM3 司马府后院, 40 seconds
- Yan Er Dao Ling, the bell thief, CAM4 范府庭院, 40 seconds, night

## How it works

1. Plan 3 to 4 segments, one action per segment
2. Generate the first clip from text only
3. Take its last frame with `ffmpeg -sseof -0.5` and use it as the first frame of the next clip, with the prompt starting "Continue this exact scene from this exact first frame"
4. State the action target exactly, for example smash the lower middle part of the side wall, not the top rim
5. Check the middle and last frame of each clip before chaining on
6. Build the finished video with `scripts/build_cctv.py`

## Files

- `SKILL.md` - the full method
- `skill.yaml` - skill metadata
- `scripts/build_cctv.py` - post production, black and white, timestamp and CAM bars, concat
- `references/storybook.md` - stories that fit, dates and CAM labels, known pitfalls

## Build

```bash
python3 scripts/build_cctv.py --workdir workspace/sima \
  --date "1026年06月18日" --cam "CAM3 司马府后院" \
  --out sima-cctv-final.mp4 \
  --clip clip1.mp4:14:20:10:00 --clip clip2.mp4:14:21:35:00
```

## Limits to know

Direct fighting, stabbing, chasing with a weapon or an animal attack is refused by the video pipeline. Show a standoff before and the result after, and let the time jump carry the fight. Breaking an object to save a person, such as smashing a vat or striking a bell, does generate.
