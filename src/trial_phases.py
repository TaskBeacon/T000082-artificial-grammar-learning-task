from __future__ import annotations

from functools import partial
from typing import Any

from psyflow import StimUnit

from .run_trial import capture_unit_response, configure_context


def _base_data(condition, trial_id, block_id, block_idx):
    return {
        "trial_id": trial_id, "phase": condition["phase"], "block_id": block_id,
        "block_idx": block_idx, "condition_id": str(condition["condition_id"]),
        "stimulus_id": str(condition["stimulus_id"]), "string": str(condition["string"]),
        "grammatical": bool(condition["grammatical"]),
    }


def _study(make_unit, settings, condition, stim_bank, trial_id, block_id, attempt, data):
    duration = float(settings.study_duration)
    unit = make_unit(unit_label=f"study_string_{attempt}").add_stim(
        stim_bank.get_and_format("letter_string", letter_string=condition["string"])
    )
    configure_context(unit, trial_id, block_id, condition, "study_string", duration, [], {
        "attempt": attempt, "training_pass": int(condition["training_pass"]),
    })
    unit.show(duration=duration, onset_trigger=settings.triggers.get("training_string")).to_dict(data)


def _capture_recall(make_unit, settings, condition, stim_bank, trial_id, block_id, attempt, data):
    typed, timed_out, submitted = "", False, False
    recall_keys = [str(key) for key in settings.recall_keys]
    submit_key, delete_key = str(settings.recall_submit_key), str(settings.recall_delete_key)
    valid_keys = [*recall_keys, delete_key, submit_key]
    allowed = {item.upper() for item in recall_keys}
    for key_index in range(int(settings.max_recall_keystrokes)):
        unit = make_unit(unit_label=f"recall_entry_{attempt}_{key_index + 1}").add_stim(
            stim_bank.get("recall_prompt"), stim_bank.get_and_format("recall_typed", typed=typed or "_")
        )
        extras = {"attempt": attempt, "typed": typed, "next_index": len(typed),
                  "target_string": str(condition["string"])}
        configure_context(unit, trial_id, block_id, condition, "recall_entry",
                          float(settings.recall_key_window), valid_keys, extras)
        capture_unit_response(unit, keys=valid_keys, duration=float(settings.recall_key_window),
            onset_trigger=settings.triggers.get("recall_entry"),
            response_trigger=settings.triggers.get("recall_key"),
            timeout_trigger=settings.triggers.get("recall_timeout"),
            terminate_on_response=True).to_dict(data)
        key = unit.get_state("response", None)
        if key is None: timed_out = True; break
        key = str(key)
        if key == submit_key: submitted = True; break
        if key == delete_key: typed = typed[:-1]
        elif key.upper() in allowed: typed += key.upper()
    return typed, submitted, timed_out


def _retry_notice(make_unit, settings, condition, stim_bank, trial_id, block_id, attempt, data):
    duration = float(settings.retry_notice_duration)
    unit = make_unit(unit_label=f"retry_notice_{attempt}").add_stim(stim_bank.get("retry_notice"))
    configure_context(unit, trial_id, block_id, condition, "retry_notice", duration, [], {"attempt": attempt})
    unit.show(duration=duration, onset_trigger=settings.triggers.get("recall_retry")).to_dict(data)


def _show_iti(make_unit, settings, condition, stim_bank, trial_id, block_id, data, label):
    duration = float(settings.iti_duration)
    unit = make_unit(unit_label=label).add_stim(stim_bank.get("fixation"))
    configure_context(unit, trial_id, block_id, condition, label, duration, [])
    unit.show(duration=duration, onset_trigger=settings.triggers.get("iti")).to_dict(data)


def _training_attempts(make_unit, settings, condition, stim_bank, trial_id, block_id, data):
    target, final_typed, correct, timed_out = str(condition["string"]).upper(), "", False, False
    max_attempts, attempt_count = int(settings.max_recall_attempts), 0
    for attempt in range(1, max_attempts + 1):
        attempt_count = attempt
        _study(make_unit, settings, condition, stim_bank, trial_id, block_id, attempt, data)
        typed, submitted, attempt_timeout = _capture_recall(
            make_unit, settings, condition, stim_bank, trial_id, block_id, attempt, data)
        final_typed, timed_out, correct = typed, timed_out or attempt_timeout, bool(submitted and typed == target)
        if correct: break
        if attempt < max_attempts:
            _retry_notice(make_unit, settings, condition, stim_bank, trial_id, block_id, attempt, data)
    return final_typed, attempt_count, correct, timed_out


def run_training_trial(*, win, kb, settings, condition, stim_bank, trigger_runtime,
                       trial_id, block_id, block_idx):
    make_unit = partial(StimUnit, win=win, kb=kb, runtime=trigger_runtime)
    data = _base_data(condition, trial_id, block_id, block_idx)
    data["training_pass"] = int(condition["training_pass"])
    typed, attempts, correct, timed_out = _training_attempts(
        make_unit, settings, condition, stim_bank, trial_id, block_id, data)
    data.update(recall_response=typed, recall_attempts=attempts, recall_correct=correct,
                recall_timeout=timed_out, response_key="", response_rt=None, correct=correct)
    _show_iti(make_unit, settings, condition, stim_bank, trial_id, block_id, data, "training_iti")
    return data


def _classification(make_unit, settings, condition, stim_bank, trial_id, block_id, data):
    grammatical = bool(condition["grammatical"])
    keys = [str(key) for key in settings.classification_keys]
    conforms_key, violates_key = keys
    correct_key = conforms_key if grammatical else violates_key
    duration = float(settings.classification_window)
    unit = make_unit(unit_label="classification").add_stim(
        stim_bank.get_and_format("test_string", letter_string=condition["string"]),
        stim_bank.get("classify_left"), stim_bank.get("classify_right"))
    configure_context(unit, trial_id, block_id, condition, "classification", duration, keys,
                      {"correct_key": correct_key})
    capture_unit_response(unit, keys=keys, duration=duration,
        onset_trigger=settings.triggers.get("test_grammatical" if grammatical else "test_nongrammatical"),
        response_trigger={conforms_key: settings.triggers.get("classify_conforms"),
                          violates_key: settings.triggers.get("classify_violates")},
        timeout_trigger=settings.triggers.get("classification_timeout"),
        correct_keys=[correct_key], terminate_on_response=True).to_dict(data)
    return unit, correct_key, conforms_key


def run_test_trial(*, win, kb, settings, condition, stim_bank, trigger_runtime,
                   trial_id, block_id, block_idx):
    make_unit = partial(StimUnit, win=win, kb=kb, runtime=trigger_runtime)
    data = _base_data(condition, trial_id, block_id, block_idx)
    data.update(source_string=str(condition.get("source_string", condition["string"])),
                violation_position=condition.get("violation_position"))
    unit, correct_key, conforms_key = _classification(
        make_unit, settings, condition, stim_bank, trial_id, block_id, data)
    response, rt = unit.get_state("response", None), unit.get_state("rt", None)
    data.update(response_key=str(response or ""),
                response_rt=float(rt) if isinstance(rt, (int, float)) else None,
                correct_key=correct_key,
                correct=None if response is None else str(response) == correct_key,
                endorsed_grammatical=None if response is None else str(response) == conforms_key)
    _show_iti(make_unit, settings, condition, stim_bank, trial_id, block_id, data, "test_iti")
    return data
