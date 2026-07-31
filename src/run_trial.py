from __future__ import annotations

from psyflow import next_trial_id, set_trial_context

from .utils import TrialSpec


_PHASE_TOKENS = {
    "study_string": "target", "recall_entry": "response", "retry_notice": "feedback",
    "classification": "decision", "training_iti": "iti", "test_iti": "iti",
}


def configure_context(unit, trial_id, block_id, condition, stage, deadline, valid_keys, extras=None):
    factors = {"stage": stage, "task_phase": condition["phase"],
               "string": condition["string"], "grammatical": bool(condition["grammatical"]),
               **(extras or {})}
    set_trial_context(
        unit, trial_id=trial_id,
        phase="target" if stage == "study_string" else _PHASE_TOKENS[stage],
        deadline_s=deadline,
        valid_keys=valid_keys, block_id=block_id,
        condition_id=str(condition["condition_id"]), task_factors=factors,
        stim_id=str(condition["stimulus_id"]),
    )


def capture_unit_response(unit, **kwargs):
    return unit.capture_response(**kwargs)

def run_trial(
    win,
    kb,
    settings,
    condition,
    stim_bank,
    trigger_runtime,
    block_id=None,
    block_idx=None,
):
    from .trial_phases import run_test_trial, run_training_trial

    if not isinstance(condition, TrialSpec):
        raise TypeError("Artificial Grammar Learning conditions must be TrialSpec objects")
    item = condition.to_dict()
    trial_id = next_trial_id()
    block_name = str(block_id or item["phase"])
    block_index = int(block_idx or 0)
    if item["phase"] == "training":
        return run_training_trial(
            win=win,
            kb=kb,
            settings=settings,
            condition=item,
            stim_bank=stim_bank,
            trigger_runtime=trigger_runtime,
            trial_id=trial_id,
            block_id=block_name,
            block_idx=block_index,
        )
    if item["phase"] == "test":
        return run_test_trial(
            win=win,
            kb=kb,
            settings=settings,
            condition=item,
            stim_bank=stim_bank,
            trigger_runtime=trigger_runtime,
            trial_id=trial_id,
            block_id=block_name,
            block_idx=block_index,
        )
    raise ValueError(f"Unsupported task phase: {item['phase']}")
