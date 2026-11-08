# Ancient CCTV Video

## Recognize the format

- Make a silent video that looks like leaked surveillance footage of an ancient Chinese story.

- Keep the camera fixed in one high angle for the whole video and never pan or zoom.

- Turn every clip black and white, add grain, burn a running date and time in the top left, put REC in the top right and put a CAM label in the bottom left.

- Tell the story with no narration and no subtitles, only with people moving in and out of frame and with jumps in the timestamp.

- Use a time jump or a short Error popup to hide a moment that cannot be shown directly, and let the next clip show the result.

- Keep the finished video 30 to 40 seconds long at 1280 by 720 and 24 frames per second.

- Copy the reference shape from the original Pan Jinlian clip from 2026-11-07, 35 seconds, CAM1 Yanggu County Zishi Street, two windows, a February 14 scene and a February 20 scene with an Error popup between them.

## Plan the story

- Pick a story the audience already knows, with one clear place and one clear turning point.

- Choose a story that works without a direct fight, or plan the fight as a standoff plus an aftermath.

- Write 3 to 4 segments of 10 seconds each, and give each segment one action only.

- Give each segment a start time that jumps forward from the last one, and keep the date and the CAM label the same for the whole video.

- Name the work folder by the story, such as workspace/wusong, workspace/sima or workspace/bell, and keep raw clips, frames and the build script inside it.

- Read references/storybook.md for stories that already fit this format and for the date and CAM label used for each one.

## Generate the clips in order

- Generate the first clip from text only with `media.generate_video`.

- Describe the first clip with the fixed camera, the place, the period clothes and the first action, and add grainy black and white CCTV footage look at the end of the prompt.

- Take the last frame of the finished clip with ffmpeg and use it as the first frame of the next clip.

- Run `ffmpeg -y -v error -sseof -0.5 -i <clip>.mp4 -vframes 1 <frames>/<clip>_last.jpg` to get that last frame.

- Generate every later clip from that image plus text with `media.generate_video`, putting the image entry first and the text entry second.

- Start the text with Continue this exact scene from this exact first frame, then name the same place, the same object and the same people, then describe the next action only.

- Never generate the segments independently from text only, because the courtyard, the object and the people will change in every clip and the story will not connect.

- Generate at most 6 videos in one user message, and count videos made by a helper agent in the same total.

## State the action target exactly

- Name the exact target of a physical action in the prompt, or the model will guess it wrong.

- Say smash the lower middle part of the side wall of the vat, and say do not throw the stone into the water and do not hit the top rim, when the action is Sima Guang smashing the vat.

- Say climb out through the crack opening in the lower side wall, and say do not climb over the top rim, when the action is the boy leaving the vat.

- Say strike the bronze bell and then cover both ears with both hands, when the action is the bell thief in the Yan Er Dao Ling story.

- Check the middle frame and the last frame of every clip with `muse.read` before you use it as the base for the next clip.

- Regenerate a clip once with a tighter target sentence when the action lands on the wrong target, and keep the clip when the target is right even if the exact contact frame is missing.

## Respect the generation limits

- Do not plan a direct fight with hitting, stabbing, chasing with a weapon or an animal attack, because the video pipeline refuses it and retrying the same idea does not help.

- Show a standoff before the fight and the result after the fight, and let the time jump carry the fight itself.

- Treat breaking an object to save a person as different from fighting a person, because smashing a vat and striking a bell both generated cleanly in November 2026.

- Say plainly when a direct action did not generate, name what the finished video shows instead, and offer a concrete alternative such as a closer side shot or a faster cut.

## Finish the video in post production

- Run `scripts/build_cctv.py` in the skill folder to turn the raw clips into the finished video, and read its help text for the exact arguments.

- Let the script turn each clip black and white with `hue=s=0`, add light contrast and grain, cover the top 92 pixels with a black bar and cover the bottom 70 pixels with a black bar when a baked timestamp sits at the bottom.

- Let the script burn the date as static text and the time as a running timecode with `drawtext`, using the Noto Sans CJK regular font at `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`.

- Escape every colon in a timecode with a backslash in the filter, such as `15\:32\:10\:00`, or ffmpeg will fail to parse the filter.

- Put the CAM label in the bottom bar and REC in the top bar, and keep the same date, CAM label and font size on every segment.

- Concatenate the finished segments in story order with the ffmpeg concat demuxer, and keep the output silent with no audio track.

- Verify the finished file with `ffprobe` for 1280 by 720, 24 frames per second and a duration near 40 seconds.

## Check the finished video

- Extract one frame from the middle of each segment and read it with `muse.read`.

- Check that the place, the main object and the main person stay the same across the cuts.

- Check that the action target is right in the middle frames, such as water bursting sideways from the side wall and not upward from the top of the vat.

- Check that no baked timestamp from the raw clips shows through the top bar or the bottom bar.

- Fix a bad segment by regenerating only that segment from the last frame of the previous good segment, then rebuild the whole video.

- Tell the user plainly what the finished video shows and what it does not show, such as a missing contact frame or a small change in camera angle between segments.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Offer a close side shot as a separate insert when the wide fixed shot cannot show a contact moment clearly.

- Offer a shorter Error popup between segments when the story needs a bigger time jump than the clips can show.

- Offer the next story from references/storybook.md when the user wants another video in the same format.
