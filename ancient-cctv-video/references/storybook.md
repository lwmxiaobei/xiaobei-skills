# Storybook for Ancient CCTV Video

Stories that fit the format, with the date and CAM label to use.
Dates below are the ones already used or a sensible story date.
Keep the same date and CAM label for all segments of one video.

## Already made

- Pan Jinlian, the original reference, 1116年02月14日, CAM1 阳谷县紫石街电杆, 35 seconds, two windows, feeding in bed, drinking in the other room, Error popup, jump to February 20.

- Wu Song fights the tiger, 1116年03月15日, CAM2 景阳冈山道, 31.5 seconds, drunk on the ridge, Error popup, standoff with the tiger, dragging the tiger away. Fight itself is never shown directly.

- Sima Guang smashes the vat, 1026年06月18日, CAM3 司马府后院, 40 seconds, children playing, boy falls into the vat, Sima Guang smashes the lower middle side of the vat, water bursts sideways, boy climbs out through the crack. Final version is v4.

- Yan Er Dao Ling, the bell thief, 前452年10月12日, CAM4 范府庭院, 40 seconds, night courtyard, man cannot lift the bell, strikes it with a hammer, covers both ears, crowd with lanterns runs in, man is led away. Baked timestamp sits at the bottom, so the bottom black bar matters.

- Cao Chong weighs the elephant, 208年03月15日, CAM5 许昌码头, 40 seconds, elephant boards the boat, official marks the waterline on the hull, elephant is led off and stones are loaded until the boat sinks to the same line, officials weigh the stones on a beam scale. First clip baked its own timestamp as CAM 03 208-03-15, covered by the top bar; the final clip used the wide retry, not the close-up boy-pointing-at-the-mark shot, to keep the fixed camera.

## Best next stories, no fight

- Cao Chong weighs the elephant, dock by the river, elephant walks onto a boat, waterline is marked, stones are loaded until the boat sinks to the same line.

- Cao Chong story date, 208年, CAM5 许昌码头.

- Grass boat borrows arrows, fog on the river, straw boats sail out, arrows rain onto the straw, boats sail back full of arrows.

- Empty city plan, a lone player plays the zither on the city wall, an army approaches and then retreats.

- Carving the mark on the boat to find the sword, a man drops his sword in the river, marks the boat, jumps in at the dock after the boat stops.

- Chang E flies to the moon, a woman in a courtyard takes the elixir and rises, use a silhouette and the moon for the flight, do not try a close flying shot.

- Three visits to the thatched cottage, snow outside the cottage, the visitor comes three times, the timestamp jumps across the three visits.

- Waiting by the tree stump, a man waits by a tree, a rabbit runs into the tree, short and comic.

- Tian Ji horse racing, a racetrack, three races, the trick is the order of the horses.

## Known pitfalls, learned in November 2026

- Independent text only segments change the courtyard, the object and the people. Always chain from the previous last frame.

- A vague smash prompt makes the model throw the stone into the vat from the top. Write the target as the lower middle part of the side wall, facing the camera, water bursting sideways from the side crack.

- A vague climb out prompt makes the boy sit beside the vat or climb over the top rim. Write the target as through the crack opening in the lower side wall, head and shoulders first, then the whole body squeezes out.

- A direct fight prompt is refused by the video pipeline, with no detail given. Do not retry it with different wording. Use a standoff before and an aftermath after.

- Generated clips often bake in a wrong timestamp or REC overlay, at the top or at the bottom. The 92 pixel top bar and the 70 pixel bottom bar in the build script cover them. Check the finished frames for any red text showing through.

- The generator may put a modern surveillance camera in the frame, as it did on the right side of the bell story. It reads as part of the joke, so keep it when it does not block the action.
