# Quality gates

Complete every gate before delivery.

## Content gate

1. The opening establishes the subject within two seconds.
2. Every scene has one narrative purpose.
3. Factual claims have been verified when the content is historical, medical, legal, financial, political, scientific, or current.
4. Names, dates, numbers, product claims, and calls to action match the approved script.
5. The ending resolves the narrative instead of stopping abruptly.

## Asset gate

1. Every referenced local asset exists.
2. Foreground subjects have clean transparency and no accidental background fragments.
3. Important characters have complete heads, hands, feet, and props.
4. Direction, scale, costume, palette, and visual style are consistent across scenes.
5. No watermark, unwanted text, or unlicensed logo appears.
6. Reconstruction imagery is not presented as documentary evidence.

## Layout gate

1. The primary subject is visually dominant.
2. Faces, hands, products, and important labels are not covered.
3. Captions remain inside platform safe areas.
4. Long text is measured or manually reviewed for overflow.
5. All scene edges are filled with no unintended transparent or black gaps.
6. The final frame remains visible long enough to read.

## Motion gate

1. All animation is driven by Remotion frames.
2. Entrances are staggered and support narrative order.
3. Background movement is subtle.
4. No element jumps because of missing clamps or invalid dimensions.
5. The frame rate and duration are consistent with `video.json`.
6. Adjacent scenes cut directly unless a deliberate transition was designed.
7. No whole scene fade reveals black, white, or the composition background between scenes.
8. Character layers show visible but restrained breathing or weight movement and do not look frozen.

## Audio gate

1. Narration is understandable and free of clipping.
2. Music remains below narration.
3. Sound effects align with visible motion.
4. No unauthorized voice cloning was used.
5. The bundled authorized reference is used by default, or a custom reference has explicit user authorization and an accurate transcript.
6. The rendered file contains the expected audio stream when narration or music was configured.
7. Narration cadence varies across clauses and does not restart with the same pitch pattern every sentence.
8. The opening, a middle scene, and the climax have been listened to after synthesis.

## Technical gate

1. `validate_project.py` exits successfully.
2. Remotion render exits successfully.
3. `inspect_video.py` reports at least one video stream.
4. Output dimensions and duration match the project configuration within normal encoding tolerance.
5. Black frame detection shows no unintended long black interval.
6. Extracted beginning, middle, and ending frames have been visually inspected.
7. Requested duration is verified with FFprobe within one video frame or unavoidable audio encoder padding.
8. A lightweight preview MP4 is generated and inspected when the main file is large.

## Delivery gate

Provide the lightweight preview first, then the full quality MP4, editable project, dimensions, duration, and known caveats. If any gate is intentionally waived, state it clearly.
