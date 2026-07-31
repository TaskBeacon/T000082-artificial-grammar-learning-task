from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Any


TRANSITIONS: dict[str, dict[str, str]] = {
    "start": {"T": "t_state", "P": "p_state"},
    "t_state": {"S": "t_state", "X": "x_state"},
    "p_state": {"T": "p_state", "V": "v_state"},
    "x_state": {"X": "p_state", "S": "end"},
    "v_state": {"P": "x_state", "V": "end"},
}


@dataclass(frozen=True)
class TrialSpec:
    phase: str
    condition_id: str
    stimulus_id: str
    string: str
    grammatical: bool
    training_pass: int | None = None
    source_string: str | None = None
    violation_position: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def is_grammatical(value: str) -> bool:
    state = "start"
    for letter in str(value).upper():
        state = TRANSITIONS.get(state, {}).get(letter, "invalid")
        if state == "invalid":
            return False
    return state == "end"


def _validate_pools(
    training_strings: list[str],
    grammatical_strings: list[str],
    nongrammatical_specs: list[dict[str, Any]],
) -> None:
    training = [str(item).upper() for item in training_strings]
    grammatical = [str(item).upper() for item in grammatical_strings]
    if len(set(training)) != len(training):
        raise ValueError("training_strings must be unique")
    if len(set(grammatical)) != len(grammatical):
        raise ValueError("test_grammatical_strings must be unique")
    if set(training) & set(grammatical):
        raise ValueError("training and grammatical test pools must be disjoint")
    if not all(is_grammatical(item) for item in training + grammatical):
        raise ValueError("all training and grammatical test strings must follow the Reber grammar")
    if len(nongrammatical_specs) != len(grammatical):
        raise ValueError("grammatical and nongrammatical test pools must be balanced")

    seen_ng: set[str] = set()
    for spec in nongrammatical_specs:
        item = str(spec["string"]).upper()
        source = str(spec["source_string"]).upper()
        position = int(spec["violation_position"])
        if source not in grammatical:
            raise ValueError(f"nongrammatical source is not in test pool: {source}")
        if item in seen_ng or is_grammatical(item):
            raise ValueError(f"invalid nongrammatical item: {item}")
        if len(item) != len(source):
            raise ValueError(f"violation length mismatch: {source} -> {item}")
        differences = [index for index, pair in enumerate(zip(item, source)) if pair[0] != pair[1]]
        if differences != [position]:
            raise ValueError(f"expected one violation at {position}: {source} -> {item}")
        seen_ng.add(item)


def generate_training_schedule(
    n_trials: int,
    condition_labels: list[Any],
    *,
    seed: int,
    training_strings: list[str],
    passes: int,
) -> list[TrialSpec]:
    del condition_labels
    items = [str(item).upper() for item in training_strings]
    if not items or not all(is_grammatical(item) for item in items):
        raise ValueError("training_strings must be non-empty grammatical Reber strings")
    if len(set(items)) != len(items):
        raise ValueError("training_strings must be unique")

    schedule: list[TrialSpec] = []
    for pass_index in range(1, int(passes) + 1):
        pass_items = list(items)
        random.Random(int(seed) + pass_index * 1009).shuffle(pass_items)
        for item_index, item in enumerate(pass_items, start=1):
            schedule.append(
                TrialSpec(
                    phase="training",
                    condition_id="training_grammatical",
                    stimulus_id=f"train_p{pass_index}_{item_index:02d}",
                    string=item,
                    grammatical=True,
                    training_pass=pass_index,
                )
            )
    if len(schedule) != int(n_trials):
        raise ValueError(f"training schedule expected {n_trials} trials, built {len(schedule)}")
    return schedule


def generate_test_schedule(
    n_trials: int,
    condition_labels: list[Any],
    *,
    seed: int,
    training_strings: list[str],
    grammatical_strings: list[str],
    nongrammatical_specs: list[dict[str, Any]],
) -> list[TrialSpec]:
    del condition_labels
    _validate_pools(training_strings, grammatical_strings, nongrammatical_specs)
    schedule: list[TrialSpec] = []
    for item_index, item in enumerate(grammatical_strings, start=1):
        schedule.append(
            TrialSpec(
                phase="test",
                condition_id="test_grammatical",
                stimulus_id=f"test_g_{item_index:02d}",
                string=str(item).upper(),
                grammatical=True,
                source_string=str(item).upper(),
            )
        )
    for item_index, raw in enumerate(nongrammatical_specs, start=1):
        schedule.append(
            TrialSpec(
                phase="test",
                condition_id="test_nongrammatical",
                stimulus_id=f"test_ng_{item_index:02d}",
                string=str(raw["string"]).upper(),
                grammatical=False,
                source_string=str(raw["source_string"]).upper(),
                violation_position=int(raw["violation_position"]),
            )
        )
    random.Random(int(seed) + 7919).shuffle(schedule)
    if len(schedule) != int(n_trials):
        raise ValueError(f"test schedule expected {n_trials} trials, built {len(schedule)}")
    return schedule


def summarize_test(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    test_rows = [row for row in rows if row.get("phase") == "test"]
    completed = [row for row in test_rows if row.get("response_key")]
    correct = [row for row in completed if row.get("correct") is True]
    grammatical = [row for row in test_rows if row.get("grammatical") is True]
    nongrammatical = [row for row in test_rows if row.get("grammatical") is False]
    hit_count = sum(row.get("response_key") == "f" for row in grammatical)
    correct_rejections = sum(row.get("response_key") == "j" for row in nongrammatical)
    rts = [float(row["response_rt"]) for row in completed if row.get("response_rt") is not None]
    return {
        "completed": len(completed),
        "correct": len(correct),
        "accuracy": len(correct) / len(completed) if completed else 0.0,
        "hit_rate": hit_count / len(grammatical) if grammatical else 0.0,
        "correct_rejection_rate": correct_rejections / len(nongrammatical) if nongrammatical else 0.0,
        "mean_rt": sum(rts) / len(rts) if rts else 0.0,
    }
