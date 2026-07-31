Use case: infographic-diagram
Asset type: TaskBeacon task flow diagram
Primary request: Create a clean, publication-ready task flow diagram as a timeline collection for the behavioral task described below.

Task: Artificial Grammar Learning Task
Construct: implicit learning / statistical learning
Rows/conditions:
- Training trial (grammatical study string followed by immediate typed reproduction; three attempts maximum)
- Grammatical test (novel string that conforms to the learned structure; correct key F)
- Nongrammatical test (paired novel string with exactly one substituted-letter violation; correct key J)

Timeline phases:
- Training trial: Study `PTVV` (3.0 s; no response; centered uppercase letter string) -> Reproduce `PTVV` (10.0 s per key event; P/T/S/X/V type, Backspace deletes, Enter submits; current typed string visible) -> Retry if incorrect (0.75 s notice, then repeat study and reproduction; 3 attempts max) -> Fixation `+` (0.5 s; no response)
- Grammatical test: Classify `PVPXVPS` (10.0 s max; F = Conforms, J = Violates; no correctness feedback) -> Fixation `+` (0.5 s; no response)
- Nongrammatical test: Classify `PVPXVVS` (10.0 s max; F = Conforms, J = Violates; no correctness feedback; one-position violation of `PVPXVPS`) -> Fixation `+` (0.5 s; no response)

Visual requirements:
- White background, landscape orientation, crisp dark text, restrained condition accent colors.
- One horizontal row per condition or representative trial type.
- Each row contains 3-7 participant-screen snapshots connected by a subtle arrow.
- Each screen snapshot shows the visible stimulus or feedback, not internal variable names.
- Use gray participant-screen boxes, thin black arrows, consistent row spacing, and subtle row separators.
- Place timing labels under each screen in compact text.
- Place condition labels at the left of each row.
- Use short labels only; avoid paragraphs inside the image.
- Make all text legible at normal document preview size.
- Leave a clean blank header band across the top 15-18% of the image. This band is reserved for a fixed title, `Construct: ...` subtitle, and TaskBeacon logo lockup that will be added after generation.

Accuracy constraints:
- Do not invent phases, stimuli, condition names, keys, rewards, or timings.
- Do not add people, lab equipment, decorative scenes, logos, or unrelated icons.
- Do not draw the task title, construct subtitle, any logo, watermark, brand mark, or `TaskBeacon` text inside the generated image.
- Draw only the timeline content below the blank header band.
- If a detail is unknown, omit it rather than guessing.
- Preserve these exact terms where used: Training trial, Grammatical test, Nongrammatical test, PTVV, PVPXVPS, PVPXVVS, F, J, Conforms, Violates, Backspace, Enter, 3.0 s, 10.0 s max, 0.75 s, 3 attempts max, 0.5 s, no feedback, 300-s interval

Style:
TaskBeacon scientific infographic style: clean vector-like raster image, organized spacing, gray screen boxes, restrained color accents, and a blank header-safe area.

Add one small, unobtrusive centered annotation between the training row and the two test rows: `300-s interval`. Do not depict it as an extra participant response phase.
