# Task Plot Brief

- Task: Artificial Grammar Learning Task
- Construct: implicit learning / statistical learning
- Canonical source: `config/config.yaml`, `src/run_trial.py`, `src/trial_phases.py`, and `README.md`
- Representative rows: one training trial, one grammatical test trial, one nongrammatical one-position-violation test trial
- Training example: `PTVV` for 3.0 s, immediate typed reproduction using P/T/S/X/V, Backspace, and Enter, optional 0.75-s retry notice with re-presentation (three attempts maximum), then 0.5-s fixation ITI
- Interphase interval: 300-s fixation between the training and test blocks
- Grammatical test example: `PVPXVPS`, F = conforms and J = violates, 10.0-s maximum, no correctness feedback, then 0.5-s fixation ITI
- Nongrammatical test example: `PVPXVVS`, a one-position violation of `PVPXVPS`, same keys/timing/no-feedback rule, then 0.5-s fixation ITI
- Accuracy-critical notes: show literal letter strings; do not draw a grammar graph; do not imply feedback after classification; test rows differ only in string grammaticality and correct key

