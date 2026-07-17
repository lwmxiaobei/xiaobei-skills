# Quality gates

## Before rendering

1. Every referenced media file exists under `public`.
2. Every video has a deliberate source interval and crop.
3. No unlooped clip is shorter than its scene.
4. Every narration sentence has a matching visual.
5. Captions remain inside the safe area and do not cover faces, products, or important UI.
6. Persistent headline, captions, and scene text do not compete for the same area.
7. Original speech and generated narration never overlap unintentionally.
8. Music and source audio are quieter than narration.
9. Total duration matches the requested target.
10. Measured narration covers at least 90 percent of narrated scene duration.
11. No narrated scene continues more than 0.60 seconds after its voiceover unless the remaining time contains deliberate source speech or an explicitly reviewed visual hold. Reject unexplained pauses above about 0.20 seconds when they make the viewer feel that the video is waiting.
12. Exact duration is reached by revising and resynthesizing narration, not by distributing missing time as silent scene padding.
13. Every caption background follows the rendered text width plus consistent horizontal padding. Short captions never sit inside a fixed full width bar.

## After rendering

1. Inspect extracted opening, middle, climax, and final frames.
2. Check every direct cut for a black or white flash.
3. Check that video clips start on useful frames and do not freeze before the scene ends.
4. Check crops for cut off faces, hands, product edges, and unreadable interfaces.
5. Listen to the opening, one middle section, and the conclusion.
6. Confirm narration cadence varies across paragraphs.
7. Confirm captions match what is spoken and contain no factual or spelling errors.
8. Confirm the final frame remains long enough to understand.
9. Deliver the lightweight preview before the full resolution file.
10. Listen across every scene boundary and reject unexplained silence after a narration clip.
