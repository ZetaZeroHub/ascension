---
name: ascension-production
description: Plan a character-driven music video, prepare consistent storyboard prompts, run bounded local ComfyUI experiments and verify beat-aware edits using the Ascension archive.
license: MIT
---

# Ascension production

Start with the music, an explicit character choice and an attainable hardware budget. Read docs/PROCESS.md and docs/REPRODUCE.md relative to the repository containing this skill.

1. Record the protagonist's identity, clothing, signature prop and motivation. Describe the story as cause and effect. Give every shot one purpose.
2. For each frame prompt specify fixed identity, one action, framing, camera position, material, light, eyeline and screen direction. State the desired end state. Do not assume more adjectives improve continuity.
3. Generate reference images before video. Compare representative frames with the user when design approval is requested. Separate image-service generation from local video generation in cost and provenance records.
4. Inspect available models and the ComfyUI node schema. Preserve both native and API workflows before submission. Record input files, seed, dimensions, frame count, steps, adapters, versions and output paths. Never claim an unexecuted workflow worked.
5. On constrained hardware use one active generation job, measure a short clip, then adjust resolution, steps and duration from evidence. Do not promise a fixed render time without a benchmark.
6. Review clip beginnings, middles, endings and motion peaks. Check identity, props, hands, direction, unintended transformations and discontinuities. Assign keep, trim, retry or reject with a reason.
7. Analyze musical onsets and phrase boundaries. Place cuts around actions and emotional changes, then inspect frames on both sides. Beat alignment alone does not establish a good cut.
8. Preserve editable timelines and imported media. Before delivery check source existence, frame rate, duration, audio alignment and a real editor preview. Version every export and avoid applying one version's checks to another.
9. For public release remove credentials and private paths, preserve license boundaries, provide asset hashes, and state which steps ran locally or through a service. Never expose original chat transcripts by default.

No step authorizes new paid services, public uploads or destructive operations beyond the user's request.
