# Style presets

Use one primary preset per video. Preserve character design, palette, line weight, lighting, and texture across all scenes.

## paper-collage

Best for history, culture, biographies, geography, and narrative explainers.

Visual rules:

1. Use textured paper, torn edges, ink drawings, restrained halftone, stamps, tape, and layered cutouts.
2. Generate backgrounds without main characters.
3. Generate characters as isolated full body transparent PNG assets with a clear facing direction.
4. Give foreground cutouts a light paper border and soft dark shadow.
5. Use slow background push, staggered character entrances, and small post entrance drift.
6. Use deep red, warm cream, ink black, muted gold, and one restrained accent color.

Prompt skeleton:

```text
[subject], [era and clothing], full body, clear [left or right] facing direction,
Chinese archival line drawing and handmade paper collage aesthetic,
warm aged paper texture, restrained muted palette, clean cutout silhouette,
transparent background, no text, no watermark, no extra people, complete hands and feet
```

## editorial-cards

Best for technology, business, productivity, commentary, and list based explainers.

Visual rules:

1. Use a clean grid, bold typography, flat cards, simple diagrams, and one accent color.
2. Prefer text and vector shapes over generated decorative imagery.
3. Keep one key statistic or idea per scene.
4. Animate cards with subtle rise or horizontal slide.
5. Use consistent margins and a large subtitle safe area.

## documentary

Best for source driven history, profiles, events, and educational content.

Visual rules:

1. Use licensed photographs, maps, documents, and restrained labels.
2. Preserve source aspect ratios and avoid decorative distortion of evidence.
3. Add slow pan and zoom only when it supports attention.
4. Put dates, places, and source labels in a stable lower corner.
5. Avoid generated imagery when it could be mistaken for authentic evidence. Label reconstructions clearly.

## product-showcase

Best for application features, physical products, and launch videos.

Visual rules:

1. Use supplied product imagery or screenshots as the primary source.
2. Keep brand colors, typography, corner radius, and logo clear space consistent.
3. Show one benefit and one supporting proof per scene.
4. Avoid generated interfaces that imply nonexistent product behavior.
5. End with a concise call to action and sufficient reading time.

## cinematic-historical-illustration

Best for historical stories that should feel like a dramatic video rather than a slide deck.

Visual rules:

1. Use a clean cinematic background plate for each location.
2. Generate important people as separate realistic transparent foreground layers with natural faces, accurate anatomy, and period appropriate clothing.
3. Preserve character face, age, hairstyle, costume, and facing direction across scenes.
4. Compose foreground people at different depths and add restrained entrance, breathing, weight shift, sway, and perspective motion.
5. Use slow background pan and push independently from foreground motion to create parallax.
6. Keep the upper title area and lower caption area visually quiet.
7. Avoid flat vector figures, chibi proportions, paper cutout borders, game character renders, readable generated text, and modern objects.

Prompt skeleton:

```text
[historical place and event], vertical cinematic historical illustration,
realistic Chinese faces and anatomy, period accurate clothing and lamellar armor,
natural skin, fabric, wood, smoke and fire texture, dramatic practical lighting,
clear depth layers, quiet title and caption areas, no text, no watermark,
no flat vector art, no cartoon, no chibi, no glossy game render
```

## Motion roles

1. `primary` has the strongest entrance and largest visual scale.
2. `secondary` enters after the primary subject with moderate movement.
3. `tertiary` uses small movement and lower contrast.
4. `static` has no entrance motion and is suitable for stable labels or structural decoration.

Keep motion subordinate to narrative hierarchy. Do not animate every element with equal intensity.
