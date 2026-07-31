# Task Logic Audit

## 1. Paradigm Intent

- Task: Artificial Grammar Learning Task (classic Reber finite-state grammar variant).
- Primary construct: implicit statistical/structural learning and grammaticality classification.
- Manipulated factors: task phase (incidental short-term-memory training vs grammaticality classification) and test grammaticality (grammatical vs one-position violation).
- Dependent measures: training reproduction accuracy and attempts; test classification accuracy, response time, hit rate, false-alarm rate, and endorsement rate.
- Key citations: Knowlton and Squire (1994, Experiments 1 and 2); Knowlton and Squire (1996, Experiment 1); Forkstam et al. (2006).

The canonical state machine is the Reber regular grammar over `{P, T, S, X, V}`:

- Start -> `T` -> T-state; Start -> `P` -> P-state.
- T-state -> `S` -> T-state (loop); T-state -> `X` -> X-state.
- P-state -> `T` -> P-state (loop); P-state -> `V` -> V-state.
- X-state -> `X` -> P-state; X-state -> `S` -> End.
- V-state -> `P` -> X-state; V-state -> `V` -> End.

This directly generates classic strings such as `TXS` and `PVPXVPS`. Test violations are constructed by replacing one nonterminal character of a grammatical test string and retaining only candidates rejected by this state machine.

## 2. Block/Trial Workflow

### Block Structure

- Total blocks: two functional blocks: incidental training followed by grammaticality classification.
- Trials per block: 32 training trials (16 grammatical strings shown in two passes) and 32 classification trials (16 grammatical, 16 one-position violations).
- Randomization/counterbalancing: the 16-item training order is independently shuffled in each pass; classification trials are shuffled with equal grammatical/nongrammatical counts. The fixed training and test pools are disjoint.
- Condition weight policy: not applicable; custom item-level schedules are required.
  - `task.condition_weights` is omitted.
  - Weight resolution is not used because the schedule must preserve disjoint fixed item pools, two complete training passes, and a 50/50 test balance.
- Condition generation method:
  - Custom generator in `src/utils.py` passed to `BlockUnit.generate_conditions(...)`.
  - Simple labels are insufficient because the concrete string, grammaticality, source pair, violation position, training pass, and stable stimulus ID must be selected before `run_trial()`.
  - Each condition is an immutable `TrialSpec` dataclass with `phase`, `condition_id`, `stimulus_id`, `string`, `grammatical`, and phase-specific fields (`training_pass` or `source_string`/`violation_position`). The immutable object is also safe for `BlockUnit` bookkeeping.
- Runtime-generated trial values:
  - No core experimental factor is chosen in `run_trial.py`.
  - The only runtime state is the participant's typed reproduction and attempt counter. All item scheduling is deterministic from the block seed.

### Trial State Machine

Training trial:

1. `study_string`
   - Onset trigger: `training_string`.
   - Stimuli shown: one centered uppercase grammatical letter string.
   - Valid keys: none.
   - Timeout behavior: string closes after 3 s.
   - Next state: `recall_entry`.
2. `recall_entry`
   - Onset trigger: `recall_entry`.
   - Stimuli shown: a Chinese prompt and the participant's currently typed uppercase reproduction.
   - Valid keys: `P`, `T`, `S`, `X`, `V`, Backspace, Enter.
   - Timeout behavior: the current attempt is marked incomplete after 10 s without a key.
   - Next state: repeat `recall_entry` after a character/backspace, or evaluate on Enter/timeout.
3. `retry_notice` (only after an incorrect attempt and before attempt 3)
   - Onset trigger: `recall_retry`.
   - Stimuli shown: neutral notice that the string will be shown again.
   - Valid keys: none.
   - Timeout behavior: advances after 0.75 s.
   - Next state: `study_string` for the next attempt.
4. `training_iti`
   - Onset trigger: `iti`.
   - Stimuli shown: fixation cross.
   - Valid keys: none.
   - Timeout behavior: advances after 0.5 s.
   - Next state: next training item.

Classification trial:

1. `classification`
   - Onset trigger: `test_grammatical` or `test_nongrammatical`.
   - Stimuli shown: one centered uppercase novel letter string, plus spatially separated response labels below it.
   - Valid keys: `F` (conforms) and `J` (does not conform).
   - Timeout behavior: missing response after 10 s; no correctness feedback.
   - Next state: `test_iti`.
2. `test_iti`
   - Onset trigger: `iti`.
   - Stimuli shown: fixation cross.
   - Valid keys: none.
   - Timeout behavior: advances after 0.5 s.
   - Next state: next classification item.

Between blocks, a 300-s neutral fixation interval implements the five-minute delay reported by Knowlton and Squire (1994), followed by test instructions that reveal the existence of the rule system and explicitly request an intuitive/gut-feeling judgment.

## 3. Condition Semantics

- Condition ID: `training_grammatical`.
  - Participant-facing meaning: an uppercase string to remember and reproduce; participants are not told that it follows a grammar.
  - Concrete stimulus realization: one of 16 fixed strings generated by the Reber state machine, shown twice across two independently shuffled passes.
  - Outcome rules: exact typed match is correct; an item can be re-presented for up to three attempts, with no rule feedback.
- Condition ID: `test_grammatical`.
  - Participant-facing meaning: a novel uppercase string that does conform to the hidden system.
  - Concrete stimulus realization: one of 16 fixed Reber strings disjoint from training.
  - Outcome rules: `F` is correct; no trial feedback.
- Condition ID: `test_nongrammatical`.
  - Participant-facing meaning: a novel uppercase string containing one rule violation.
  - Concrete stimulus realization: a one-position substitution of a paired grammatical test item, verified to be rejected by the state machine.
  - Outcome rules: `J` is correct; no trial feedback.

Participant-facing text source: all instructions, labels, prompts, and notices are defined in `config/*.yaml`; `run_trial.py` only formats config-defined stimuli. This supports Chinese localization without code edits.

## 4. Response and Scoring Rules

- Response mapping: training reproduction uses `P/T/S/X/V`, Backspace, and Enter; classification uses `F = conforms` and `J = does not conform`.
- Response key source: `task.recall_keys`, `task.recall_submit_key`, `task.recall_delete_key`, and `task.classification_keys` in config.
- Missing-response policy: a training key timeout ends the current attempt; a classification timeout records no response and `correct = null`.
- Correctness logic: training requires exact string equality; classification compares the chosen key to grammaticality.
- Reward/penalty updates: none.
- Running metrics: completed test trials, correct classifications, grammatical hit rate, nongrammatical correct-rejection rate, overall accuracy, and mean classification RT.

## 5. Stimulus Layout Plan

- Screen name: `study_string`.
  - Stimulus IDs shown together: `training_string`.
  - Layout anchors: string centered at `[0, 0]`.
  - Size/spacing: uppercase monospaced text, height 1.2 deg.
  - Readability/overlap checks: one element only; maximum eight-character study strings fit comfortably at 1280x800.
  - Rationale: reproduces the single index-card/string presentation used in the cited studies.
- Screen name: `recall_entry`.
  - Stimulus IDs shown together: `recall_prompt`, `recall_typed`.
  - Layout anchors: prompt `[0, 2.2]`, typed response `[0, -0.2]`.
  - Size/spacing: prompt height 0.62 deg with 24-deg wrap; typed string height 1.1 deg.
  - Readability/overlap checks: vertical separation exceeds combined text heights; verified in QA screenshots.
  - Rationale: makes the immediate reproduction task explicit without revealing grammar rules.
- Screen name: `classification`.
  - Stimulus IDs shown together: `test_string`, `classify_left`, `classify_right`.
  - Layout anchors: string `[0, 1.2]`; response labels `[-5.0, -2.5]` and `[5.0, -2.5]`.
  - Size/spacing: string height 1.2 deg; each response label height 0.6 deg, wrap width 8 deg.
  - Readability/overlap checks: labels are separated by 10 deg and remain below the string.
  - Rationale: unambiguous forced-choice layout with stable left/right key mapping.

## 6. Trigger Plan

- `experiment_start` / `experiment_end`: session boundaries.
- `training_block_start` / `training_block_end`: incidental learning block.
- `training_string`: onset of every grammatical training string.
- `recall_entry`: each reproduction key-entry screen.
- `recall_key`: accepted letter/backspace/submit response.
- `recall_timeout`: missing key during reproduction.
- `recall_retry`: re-presentation notice after an incorrect attempt.
- `delay_start` / `delay_end`: five-minute interphase interval.
- `test_block_start` / `test_block_end`: grammaticality classification block.
- `test_grammatical` / `test_nongrammatical`: test-string onset by true class.
- `classify_conforms` / `classify_violates`: F/J response.
- `classification_timeout`: no classification response.
- `iti`: fixation interval.

## 7. Architecture Decisions (Auditability)

- `main.py` runtime flow style: one explicit mode-aware flow that visibly runs training, delay, test instructions, classification, summary, and data export.
- `utils.py` used: yes.
- Exact purpose: define/validate the Reber finite-state machine, construct deterministic disjoint item schedules from config pools, and compute summary metrics.
- Custom controller used: no.
- Legacy/backward-compatibility fallback logic required: no.

## 8. Inference Log

- Decision: use 16 fixed training strings shown twice and 32 test strings rather than a patient-study-specific 23/23 set.
  - Why inference was required: the complete Experiment 1 item lists are not printed in the accessible article body, while Experiment 2 explicitly uses a 16-item training set and 32-item test set.
  - Citation-supported rationale: Knowlton and Squire (1994), Experiment 2 materials and procedure; Forkstam et al. (2006) supports fixed, disjoint acquisition/classification sets and 50/50 grammaticality.
- Decision: impose a 10-s per-key training deadline and a 10-s classification deadline.
  - Why inference was required: the classic index-card studies were self-paced after the fixed 3-s study display and did not report a computerized response timeout.
  - Citation-supported rationale: conservative computerized implementation that preserves the response content and does not alter grammaticality or feedback logic.
- Decision: use Chinese participant-facing instructions and SimHei while preserving the cited Latin-letter stimuli.
  - Why inference was required: TaskBeacon's default language policy is Chinese, whereas the source studies used English/Dutch instructions.
  - Citation-supported rationale: participant instructions are localized, but the canonical letter alphabet and grammar are unchanged.
- Decision: use whole-string display during classification rather than Forkstam et al.'s sequential fMRI presentation.
  - Why inference was required: this task is the classic behavioral variant, not the scanner-specific variant.
  - Citation-supported rationale: Knowlton and Squire (1994, 1996) used whole strings on index cards; Forkstam et al. (2006) is used for grammar/material construction evidence, not scanner timing.
