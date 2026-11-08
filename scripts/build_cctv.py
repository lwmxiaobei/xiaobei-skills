#!/usr/bin/env python3
"""Build an ancient CCTV video from raw AI clips.

Usage:
  python3 build_cctv.py --workdir workspace/sima \
    --date "1026年06月18日" --cam "CAM3 司马府后院" \
    --out sima-cctv-final.mp4 \
    --clip clip1.mp4:14:20:10:00 --clip clip2.mp4:14:21:35:00

Each --clip takes a raw clip file inside --workdir plus a start
timecode in HH:MM:SS:FF form. The script turns each clip black and
white, covers the top 92 pixels and the bottom 70 pixels with black
bars, burns the date and the running timecode in the top bar, burns
the CAM label in the bottom bar, then concatenates the segments in
order into a silent 1280x720 24fps mp4.

The bottom bar hides baked timestamps that some generators put at
the bottom of the frame, such as CAM 01 1998-03-15 23:42:14 in the
bell story. When a story has no baked timestamp at the bottom, the
bottom bar still gives the video a uniform CCTV frame.
"""
import argparse
import os
import subprocess
import sys

FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def run(cmd):
    print("RUN:", cmd[-1])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-2000:])
        print(result.stderr[-3000:])
        sys.exit("ffmpeg failed")
    return result


def escape_timecode(timecode):
    return timecode.replace(":", "\\:")


def parse_clip(spec):
    if ".mp4:" not in spec:
        raise ValueError("each --clip must look like file.mp4:14:20:10:00")
    src, timecode = spec.split(".mp4:", 1)
    return src + ".mp4", timecode


def main():
    parser = argparse.ArgumentParser(description="Build an ancient CCTV video")
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--date", required=True, help="Date text, such as 1026年06月18日")
    parser.add_argument("--cam", required=True, help="CAM label, such as CAM3 司马府后院")
    parser.add_argument("--out", required=True, help="Output file name inside workdir")
    parser.add_argument("--clip", required=True, action="append",
                        help="file.mp4:HH:MM:SS:FF, repeat once per segment in story order")
    args = parser.parse_args()

    workdir = args.workdir
    segments = []
    for index, spec in enumerate(args.clip, start=1):
        try:
            src, timecode = parse_clip(spec)
        except ValueError as exc:
            parser.error(str(exc))
        out = f"seg{index}.mp4"
        segments.append(out)
        vf = (
            "hue=s=0,eq=contrast=1.05:brightness=-0.02,noise=alls=5:allf=t,"
            "drawbox=x=0:y=0:w=1280:h=92:color=black:t=fill,"
            "drawbox=x=0:y=650:w=1280:h=70:color=black:t=fill,"
            f"drawtext=fontfile={FONT}:text='{args.date}':fontcolor=white:fontsize=26:x=20:y=16,"
            f"drawtext=fontfile={FONT}:timecode='{escape_timecode(timecode)}':rate=24:fontcolor=white:fontsize=26:x=340:y=16,"
            f"drawtext=fontfile={FONT}:text='REC':fontcolor=red:fontsize=26:x=1180:y=16,"
            f"drawtext=fontfile={FONT}:text='{args.cam}':fontcolor=white:fontsize=26:x=20:y=668"
        )
        run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(workdir, src),
             "-vf", vf, "-r", "24", "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-an", os.path.join(workdir, out)])

    concat_path = os.path.join(workdir, "concat.txt")
    with open(concat_path, "w", encoding="utf-8") as f:
        for name in segments:
            f.write(f"file '{name}'\n")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", concat_path, "-c", "copy", os.path.join(workdir, args.out)])
    print("done")


if __name__ == "__main__":
    main()
