from __future__ import annotations

from contextlib import nullcontext
from functools import partial
from pathlib import Path

import pandas as pd
from psychopy import core
from psyflow import (
    BlockUnit,
    StimBank,
    StimUnit,
    SubInfo,
    TaskRunOptions,
    TaskSettings,
    context_from_config,
    initialize_exp,
    initialize_triggers,
    load_config,
    parse_task_run_options,
    runtime_context,
)

from src.run_trial import run_trial
from src.utils import generate_test_schedule, generate_training_schedule, summarize_test

MODES = ("human", "qa", "sim")
DEFAULT_CONFIG_BY_MODE = {
    "human": "config/config.yaml",
    "qa": "config/config_qa.yaml",
    "sim": "config/config_scripted_sim.yaml",
}


def _instruction(stim_bank, name: str, win, kb, trigger_runtime) -> None:
    StimUnit(name, win, kb, runtime=trigger_runtime).add_stim(
        stim_bank.get(name)
    ).wait_and_continue()


def run(options: TaskRunOptions) -> None:
    root = Path(__file__).resolve().parent
    config = load_config(str(options.config_path))
    output_dir, scope, context = None, nullcontext(), None
    if options.mode in ("qa", "sim"):
        context = context_from_config(task_dir=root, config=config, mode=options.mode)
        output_dir, scope = context.output_dir, runtime_context(context)

    with scope:
        if options.mode == "qa":
            subject = {"subject_id": "qa"}
        elif options.mode == "sim":
            subject = {"subject_id": str(context.session.participant_id or "sim")}
        else:
            subject = SubInfo(config["subform_config"]).collect()

        settings = TaskSettings.from_dict(config["task_config"])
        settings.add_subinfo(subject)
        if output_dir is not None:
            settings.save_path = str(output_dir)
        if options.mode == "qa" and output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            settings.res_file = str(output_dir / "qa_trace.csv")
            settings.log_file = str(output_dir / "qa_psychopy.log")
            settings.json_file = str(output_dir / "qa_settings.json")

        settings.triggers = config["trigger_config"]
        triggers = (
            initialize_triggers(mock=True)
            if options.mode in ("qa", "sim")
            else initialize_triggers(config)
        )
        win, kb = initialize_exp(settings)
        bank = StimBank(win, config["stim_config"]).preload_all()
        settings.save_to_json()
        triggers.send(settings.triggers.get("experiment_start"))

        _instruction(bank, "training_instruction", win, kb, triggers)
        rows: list[dict] = []
        training_n = len(settings.training_strings) * int(settings.training_passes)
        training_block = (
            BlockUnit(
                block_id="training",
                block_idx=0,
                settings=settings,
                window=win,
                keyboard=kb,
                n_trials=training_n,
            )
            .generate_conditions(
                func=generate_training_schedule,
                n_trials=training_n,
                condition_labels=["training_grammatical"],
                training_strings=list(settings.training_strings),
                passes=int(settings.training_passes),
            )
            .on_start(lambda _: triggers.send(settings.triggers.get("training_block_start")))
            .on_end(lambda _: triggers.send(settings.triggers.get("training_block_end")))
            .run_trial(
                partial(
                    run_trial,
                    stim_bank=bank,
                    trigger_runtime=triggers,
                    block_id="training",
                    block_idx=0,
                )
            )
        )
        training_block.to_dict(rows)

        delay = StimUnit("interphase_delay", win, kb, runtime=triggers).add_stim(
            bank.get("delay_fixation")
        )
        delay.show(
            duration=float(settings.interphase_delay),
            onset_trigger=settings.triggers.get("delay_start"),
        )
        triggers.send(settings.triggers.get("delay_end"))

        _instruction(bank, "test_instruction", win, kb, triggers)
        test_n = len(settings.test_grammatical_strings) + len(settings.test_nongrammatical)
        test_block = (
            BlockUnit(
                block_id="test",
                block_idx=1,
                settings=settings,
                window=win,
                keyboard=kb,
                n_trials=test_n,
            )
            .generate_conditions(
                func=generate_test_schedule,
                n_trials=test_n,
                condition_labels=["test_grammatical", "test_nongrammatical"],
                training_strings=list(settings.training_strings),
                grammatical_strings=list(settings.test_grammatical_strings),
                nongrammatical_specs=list(settings.test_nongrammatical),
            )
            .on_start(lambda _: triggers.send(settings.triggers.get("test_block_start")))
            .on_end(lambda _: triggers.send(settings.triggers.get("test_block_end")))
            .run_trial(
                partial(
                    run_trial,
                    stim_bank=bank,
                    trigger_runtime=triggers,
                    block_id="test",
                    block_idx=1,
                )
            )
        )
        test_block.to_dict(rows)

        summary = summarize_test(rows)
        StimUnit("good_bye", win, kb, runtime=triggers).add_stim(
            bank.get_and_format(
                "good_bye",
                completed=summary["completed"],
                total=test_n,
                correct=summary["correct"],
                accuracy=summary["accuracy"],
                mean_rt=summary["mean_rt"],
            )
        ).wait_and_continue(terminate=True)

        triggers.send(settings.triggers.get("experiment_end"))
        pd.DataFrame(rows).to_csv(settings.res_file, index=False)
        triggers.close()
        core.quit()


def main() -> None:
    run(
        parse_task_run_options(
            task_root=Path(__file__).resolve().parent,
            description="Run the Artificial Grammar Learning Task",
            default_config_by_mode=DEFAULT_CONFIG_BY_MODE,
            modes=MODES,
        )
    )


if __name__ == "__main__":
    main()
