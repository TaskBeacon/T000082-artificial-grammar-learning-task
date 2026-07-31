from __future__ import annotations

import random as _random
from dataclasses import dataclass, field
from typing import Any

from psyflow.sim.contracts import Action


def _phase(observation) -> tuple[str, dict[str, Any], list[str]]:
    factors = dict(getattr(observation, "task_factors", {}) or {})
    phase = str(factors.get("stage", getattr(observation, "phase", "")))
    keys = [str(key) for key in (getattr(observation, "valid_keys", None) or [])]
    return phase, factors, keys


class ScriptedResponder:
    """Deterministic responder covering exact recall and both test classes."""

    def start_session(self, session, rng) -> None:
        self.rng = rng

    def on_feedback(self, feedback) -> None:
        return None

    def end_session(self) -> None:
        return None

    def act(self, observation) -> Action:
        phase, factors, keys = _phase(observation)
        if not keys:
            return Action(key=None, rt_s=None)
        if phase == "recall_entry":
            target = str(factors.get("target_string", "")).lower()
            typed = str(factors.get("typed", ""))
            key = target[len(typed)] if len(typed) < len(target) else "return"
            return Action(key=key, rt_s=0.02)
        if phase == "classification":
            return Action(key=str(factors.get("correct_key", keys[0])), rt_s=0.02)
        if "space" in keys:
            return Action(key="space", rt_s=0.02)
        return Action(key=keys[0], rt_s=0.02)


@dataclass
class TaskSamplerResponder:
    classification_accuracy: float = 0.8
    recall_accuracy: float = 0.85
    rt_mean_s: float = 0.45
    rt_sd_s: float = 0.08
    _rng: Any = field(default=None, init=False, repr=False)
    _recall_success: dict[str, bool] = field(default_factory=dict, init=False, repr=False)

    def start_session(self, session, rng) -> None:
        self._rng = rng

    def on_feedback(self, feedback) -> None:
        return None

    def end_session(self) -> None:
        self._rng = None
        self._recall_success.clear()

    def _random(self) -> float:
        return float(self._rng.random()) if self._rng is not None else _random.random()

    def _gauss(self) -> float:
        if self._rng is not None and hasattr(self._rng, "normal"):
            return float(self._rng.normal(self.rt_mean_s, self.rt_sd_s))
        if self._rng is not None and hasattr(self._rng, "gauss"):
            return float(self._rng.gauss(self.rt_mean_s, self.rt_sd_s))
        return float(_random.gauss(self.rt_mean_s, self.rt_sd_s))

    def act(self, observation) -> Action:
        phase, factors, keys = _phase(observation)
        if not keys:
            return Action(key=None, rt_s=None)
        rt = max(0.12, self._gauss())
        if phase == "recall_entry":
            trial_id = str(getattr(observation, "trial_id", "trial"))
            if trial_id not in self._recall_success:
                self._recall_success[trial_id] = self._random() <= float(self.recall_accuracy)
            target = str(factors.get("target_string", "")).lower()
            typed = str(factors.get("typed", ""))
            if len(typed) >= len(target):
                return Action(key="return", rt_s=rt)
            key = target[len(typed)]
            if not self._recall_success[trial_id] and len(typed) == max(0, len(target) // 2):
                alternatives = [item for item in "ptsxv" if item != key]
                key = alternatives[0]
            return Action(key=key, rt_s=rt)
        if phase == "classification":
            correct_key = str(factors.get("correct_key", keys[0]))
            if self._random() <= float(self.classification_accuracy):
                key = correct_key
            else:
                key = next(item for item in keys if item != correct_key)
            return Action(key=key, rt_s=rt)
        if "space" in keys:
            return Action(key="space", rt_s=0.15)
        return Action(key=keys[0], rt_s=rt)
