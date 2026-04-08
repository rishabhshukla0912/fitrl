"""
app_ui.py — Gradio frontend to run and inspect the Life Optimization environment.

Usage:
    pip install gradio
    python app_ui.py
"""

import asyncio
import json
import os
from uuid import uuid4

import gradio as gr

import inference as inf_module
from inference import (
    API_BASE_URL,
    MODEL_NAME,
    ENV_BASE_URL,
    SUCCESS_SCORE_THRESHOLD,
    TASK_SPECS,
    get_llm_action,
    run_episode,
)
from client import FitrlEnv
from models import (
    EffortLevel,
    FitnessAction,
    IntensityLevel,
    LifeOptimizationAction,
    TaskType,
    WorkAction,
    WorkoutType,
)
from openai import OpenAI


TASK_NAMES = [task.name for task in TASK_SPECS]
_MANUAL_ENVS = {}


def _configure_runtime(api_key: str, api_base: str, model: str, env_url: str):
    api_key = api_key.strip()
    api_base = api_base.strip()
    model = model.strip()
    env_url = env_url.strip()

    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["API_KEY"] = api_key
    os.environ["HF_TOKEN"] = api_key
    os.environ["API_BASE_URL"] = api_base
    os.environ["MODEL_NAME"] = model
    os.environ["ENV_BASE_URL"] = env_url

    inf_module.API_KEY = api_key
    inf_module.API_BASE_URL = api_base
    inf_module.MODEL_NAME = model
    inf_module.ENV_BASE_URL = env_url

    return api_key, api_base, model, env_url


def _json_text(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    return json.dumps(value, indent=2, sort_keys=True)


def _build_score_table(scores: dict) -> str:
    rows = []
    for task, score in scores.items():
        status = "PASS" if score >= SUCCESS_SCORE_THRESHOLD else "FAIL"
        rows.append(f"| {task:<25} | {score:.3f} | {status} |")
    header = "| Task                      | Score | Status |\n|---------------------------|-------|--------|"
    return header + "\n" + "\n".join(rows)


def _build_status(scores: dict) -> str:
    if not scores:
        return "Running..."
    passing = sum(1 for s in scores.values() if s >= SUCCESS_SCORE_THRESHOLD)
    total = len(scores)
    return f"{passing}/{total} tasks passing (threshold: {SUCCESS_SCORE_THRESHOLD})"


def _run_task(api_key: str, api_base: str, model: str, env_url: str, task_name: str):
    api_key, api_base, model, env_url = _configure_runtime(api_key, api_base, model, env_url)
    client = OpenAI(base_url=api_base, api_key=api_key) if api_key else None
    env = FitrlEnv(base_url=env_url)

    async def _run():
        log_lines = []
        episode_result = None
        original_log_step = inf_module.log_step
        original_log_end = inf_module.log_end
        original_log_start = inf_module.log_start

        def capture_start(task, env, model):
            log_lines.append(f"[START] task={task} env={env} model={model}")

        def capture_step(step, action, reward, done, error):
            err = error if error else "null"
            line = (
                f"[STEP] step={step} action={action} reward={reward:.2f} "
                f"done={str(done).lower()} error={err}"
            )
            log_lines.append(line)

        def capture_end(success, steps, score, rewards):
            rewards_str = ",".join(f"{r:.2f}" for r in rewards)
            line = (
                f"[END] success={str(success).lower()} steps={steps} "
                f"score={score:.3f} rewards={rewards_str}"
            )
            log_lines.append(line)

        inf_module.log_start = capture_start
        inf_module.log_step = capture_step
        inf_module.log_end = capture_end

        try:
            episode_result = await run_episode(env, client, task_name)
        finally:
            if episode_result is None:
                episode_result = inf_module.EpisodeResult(
                    steps_taken=0,
                    rewards=[],
                    score=0.0,
                    success=False,
                )
            try:
                await env.close()
            except Exception:
                pass
            capture_end(
                episode_result.success,
                episode_result.steps_taken,
                episode_result.score,
                episode_result.rewards,
            )
            inf_module.log_start = original_log_start
            inf_module.log_step = original_log_step
            inf_module.log_end = original_log_end

        return episode_result.score, log_lines

    return asyncio.run(_run())


def run_selected_task(api_key: str, api_base: str, model: str, env_url: str, task_name: str):
    score, log_lines = _run_task(api_key, api_base, model, env_url, task_name)
    scores = {task_name: score}
    return "\n".join(log_lines), _build_score_table(scores), _build_status(scores)


def run_all_tasks(api_key: str, api_base: str, model: str, env_url: str):
    all_logs = []
    scores = {}

    for task_name in TASK_NAMES:
        score, log_lines = _run_task(api_key, api_base, model, env_url, task_name)
        scores[task_name] = score
        all_logs.extend([f"\n--- Task: {task_name} ---"] + log_lines)

    return "\n".join(all_logs), _build_score_table(scores), _build_status(scores)


def _append_log(existing: str, line: str) -> str:
    if not existing.strip():
        return line
    return existing.rstrip() + "\n" + line


def _close_manual_env(session: dict | None) -> None:
    if not session:
        return
    session_id = session.get("session_id")
    env = _MANUAL_ENVS.pop(session_id, None)
    if env is None:
        return
    try:
        env.close()
    except Exception:
        pass


def _ensure_manual_env(session: dict | None, env_url: str, task_name: str):
    env_url = env_url.strip()
    session = dict(session or {})
    session_id = session.get("session_id")
    env = _MANUAL_ENVS.get(session_id) if session_id else None

    if env is None or session.get("env_url") != env_url:
        _close_manual_env(session)
        session_id = str(uuid4())
        env = FitrlEnv(base_url=env_url).sync()
        _MANUAL_ENVS[session_id] = env
        session = {
            "session_id": session_id,
            "env_url": env_url,
            "task_name": task_name,
            "last_observation": None,
        }

    session["task_name"] = task_name
    return env, session


def _snapshot(session: dict, env, status: str, log_text: str, result=None):
    observation = session.get("last_observation")
    if result is not None:
        observation = result.observation.model_dump()
        session["last_observation"] = observation

    state_value = None
    try:
        state_value = env.state()
    except Exception:
        state_value = None

    reward = ""
    done = ""
    phase = ""
    if observation:
        reward = f"{observation.get('reward', 0.0):.2f}"
        done = str(observation.get("done", False)).lower()
        phase = observation.get("time_of_day", "")

    return (
        session,
        status,
        phase,
        reward,
        done,
        _json_text(observation),
        _json_text(state_value),
        log_text,
    )


def manual_reset(session: dict, manual_log: str, env_url: str, task_name: str):
    env, session = _ensure_manual_env(session, env_url, task_name)
    result = env.reset()
    log_text = _append_log(manual_log, f"reset task={task_name}")
    status = f"Reset complete for {task_name}."
    return _snapshot(session, env, status, log_text, result=result)


def manual_state(session: dict, manual_log: str, env_url: str, task_name: str):
    env, session = _ensure_manual_env(session, env_url, task_name)
    log_text = _append_log(manual_log, f"state task={task_name}")
    status = f"Fetched state for {task_name}."
    return _snapshot(session, env, status, log_text)


def _build_custom_action(
    phase: str,
    workout_type: str,
    intensity: str,
    duration: float,
    work_task: str,
    effort_level: str,
):
    if phase == "morning":
        return LifeOptimizationAction(
            fitness_action=FitnessAction(
                workout_type=WorkoutType(workout_type),
                intensity=IntensityLevel(intensity),
                duration=int(duration or 0),
            )
        )
    if phase == "afternoon":
        return LifeOptimizationAction(
            work_action=WorkAction(
                task_type=TaskType(work_task),
                effort_level=EffortLevel(effort_level),
            )
        )
    return LifeOptimizationAction()


def manual_custom_step(
    session: dict,
    manual_log: str,
    env_url: str,
    task_name: str,
    workout_type: str,
    intensity: str,
    duration: float,
    work_task: str,
    effort_level: str,
):
    env, session = _ensure_manual_env(session, env_url, task_name)
    observation = session.get("last_observation")
    if not observation:
        return _snapshot(
            session,
            env,
            "Reset the environment before calling step().",
            manual_log,
        )

    phase = observation.get("time_of_day", "morning")
    action = _build_custom_action(phase, workout_type, intensity, duration, work_task, effort_level)
    result = env.step(action)
    action_payload = {k: v for k, v in action.model_dump().items() if v is not None}
    log_text = _append_log(
        manual_log,
        f"step task={task_name} phase={phase} action={json.dumps(action_payload)} "
        f"reward={(result.reward or 0.0):.2f} done={str(result.done).lower()}",
    )
    status = f"Custom step complete for {task_name}."
    return _snapshot(session, env, status, log_text, result=result)


def manual_task_step(
    session: dict,
    manual_log: str,
    api_key: str,
    api_base: str,
    model: str,
    env_url: str,
    task_name: str,
):
    env, session = _ensure_manual_env(session, env_url, task_name)
    observation = session.get("last_observation")
    if not observation:
        return _snapshot(
            session,
            env,
            "Reset the environment before running a task step.",
            manual_log,
        )

    api_key, api_base, model, env_url = _configure_runtime(api_key, api_base, model, env_url)
    state_value = env.state()
    step_number = state_value.step_count + 1
    if api_key:
        client = OpenAI(base_url=api_base, api_key=api_key)
        action = get_llm_action(client, observation, step_number, task_name)
    else:
        action = inf_module._baseline_action(observation, task_name)

    result = env.step(action)
    action_payload = {k: v for k, v in action.model_dump().items() if v is not None}
    action_source = "llm" if api_key else "baseline"
    log_text = _append_log(
        manual_log,
        f"task_step task={task_name} source={action_source} step={step_number} "
        f"action={json.dumps(action_payload)} reward={(result.reward or 0.0):.2f} "
        f"done={str(result.done).lower()}",
    )
    status = f"Task step complete for {task_name} using {action_source} policy."
    return _snapshot(session, env, status, log_text, result=result)


def manual_close(session: dict, manual_log: str):
    _close_manual_env(session)
    status = "Closed manual environment session."
    log_text = _append_log(manual_log, "close session")
    return {}, status, "", "", "", "", "", log_text


with gr.Blocks(title="Life Optimization Agent", theme=gr.themes.Soft()) as demo:
    manual_session = gr.State({})

    gr.Markdown("# Life Optimization Agent")
    gr.Markdown("Run a selected task with an OpenAI-backed policy, or leave the API key blank to reproduce the deterministic baseline policy.")

    with gr.Row():
        with gr.Column(scale=1):
            api_key = gr.Textbox(
                label="API Key",
                placeholder="Optional: OpenAI or provider key",
                type="password",
            )
            api_base = gr.Textbox(
                label="API Base URL",
                value=API_BASE_URL,
            )
            model = gr.Textbox(
                label="Model Name",
                value=MODEL_NAME,
            )
            env_url = gr.Textbox(
                label="Env Server URL",
                value=ENV_BASE_URL,
            )
            task_name = gr.Dropdown(
                label="Task",
                choices=TASK_NAMES,
                value=TASK_NAMES[0],
            )
            with gr.Row():
                run_task_btn = gr.Button("Run Selected Task", variant="primary")
                run_all_btn = gr.Button("Run All Tasks")

        with gr.Column(scale=2):
            status_box = gr.Textbox(label="Run Status", interactive=False)
            score_table = gr.Markdown(label="Scores")
            run_log_box = gr.Textbox(
                label="Run Logs",
                lines=18,
                max_lines=40,
                interactive=False,
            )

    with gr.Accordion("Manual Session", open=True):
        gr.Markdown("Use `reset()`, `state()`, and either a task-driven or custom `step()` against one persistent environment session.")

        with gr.Row():
            reset_btn = gr.Button("Reset")
            task_step_btn = gr.Button("Task Step", variant="primary")
            custom_step_btn = gr.Button("Custom Step")
            state_btn = gr.Button("State")
            close_btn = gr.Button("Close Session")

        with gr.Row():
            with gr.Column():
                workout_type = gr.Dropdown(
                    label="Morning workout_type",
                    choices=[value.value for value in WorkoutType],
                    value=WorkoutType.strength.value,
                )
                intensity = gr.Dropdown(
                    label="Morning intensity",
                    choices=[value.value for value in IntensityLevel],
                    value=IntensityLevel.medium.value,
                )
                duration = gr.Number(
                    label="Morning duration",
                    value=30,
                    precision=0,
                )
            with gr.Column():
                work_task = gr.Dropdown(
                    label="Afternoon task_type",
                    choices=[value.value for value in TaskType],
                    value=TaskType.deep_work.value,
                )
                effort_level = gr.Dropdown(
                    label="Afternoon effort_level",
                    choices=[value.value for value in EffortLevel],
                    value=EffortLevel.medium.value,
                )

        with gr.Row():
            manual_status = gr.Textbox(label="Manual Status", interactive=False)
            current_phase = gr.Textbox(label="Current Phase", interactive=False)
            last_reward = gr.Textbox(label="Last Reward", interactive=False)
            done_box = gr.Textbox(label="Done", interactive=False)

        with gr.Row():
            observation_box = gr.Code(label="Observation", language="json", interactive=False)
            state_box = gr.Code(label="State", language="json", interactive=False)

        manual_log = gr.Textbox(
            label="Manual Log",
            lines=12,
            max_lines=24,
            interactive=False,
        )

    run_task_btn.click(
        fn=run_selected_task,
        inputs=[api_key, api_base, model, env_url, task_name],
        outputs=[run_log_box, score_table, status_box],
    )

    run_all_btn.click(
        fn=run_all_tasks,
        inputs=[api_key, api_base, model, env_url],
        outputs=[run_log_box, score_table, status_box],
    )

    reset_btn.click(
        fn=manual_reset,
        inputs=[manual_session, manual_log, env_url, task_name],
        outputs=[manual_session, manual_status, current_phase, last_reward, done_box, observation_box, state_box, manual_log],
    )

    state_btn.click(
        fn=manual_state,
        inputs=[manual_session, manual_log, env_url, task_name],
        outputs=[manual_session, manual_status, current_phase, last_reward, done_box, observation_box, state_box, manual_log],
    )

    task_step_btn.click(
        fn=manual_task_step,
        inputs=[manual_session, manual_log, api_key, api_base, model, env_url, task_name],
        outputs=[manual_session, manual_status, current_phase, last_reward, done_box, observation_box, state_box, manual_log],
    )

    custom_step_btn.click(
        fn=manual_custom_step,
        inputs=[
            manual_session,
            manual_log,
            env_url,
            task_name,
            workout_type,
            intensity,
            duration,
            work_task,
            effort_level,
        ],
        outputs=[manual_session, manual_status, current_phase, last_reward, done_box, observation_box, state_box, manual_log],
    )

    close_btn.click(
        fn=manual_close,
        inputs=[manual_session, manual_log],
        outputs=[manual_session, manual_status, current_phase, last_reward, done_box, observation_box, state_box, manual_log],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
