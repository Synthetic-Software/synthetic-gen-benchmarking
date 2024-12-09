from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from sweagent.types import AgentInfo, TrajectoryStep

from helpers.classes import UnsolvedIssue, IssueSolution, MinerModelStats, ScriptArguments, ActionsArguments


from sweagent.agent.agents import Agent
from sweagent.agent.agents import AgentArguments
from sweagent.agent.models import ModelArguments
from sweagent.environment.swe_env import EnvironmentArguments
from sweagent.environment.swe_env import SWEEnv
from sweagent.environment.utils import (
    get_data_path_name,
)

logger = logging.getLogger(__name__)


def create_script_arguments(model_name: str, unsolved_issue: UnsolvedIssue) -> ScriptArguments:
    swe_agent_root = Path("../SWE-agent")
    return ScriptArguments(
        environment=EnvironmentArguments(
            image_name="sweagent/swe-agent:latest",
            data_path=f"text://{unsolved_issue.desc}",
            repo_path=str(unsolved_issue.local_code_path),
            verbose=True,
            install_environment=True,
            environment_setup=swe_agent_root / "config/environment_setup/seaborn.yaml"
        ),
        skip_existing=False,
        agent=AgentArguments(
            model=ModelArguments(
                model_name= model_name,
            ),
            config_file=Path(swe_agent_root / "config/default_from_url.yaml"),
        ),
        actions=ActionsArguments(
            open_pr=False,
            skip_if_commits_reference_issue=False,
            apply_patch_locally=True,
        ),
        print_config=True,
    )

def generate_code_patch(model_name: str, unsolved_issue: UnsolvedIssue) -> IssueSolution:
    script_arguments = create_script_arguments(model_name, unsolved_issue)

    env = SWEEnv(script_arguments.environment)
    observation, info = env.reset(0)

    agent = Agent("primary", script_arguments.agent)
    trajectories_dir = Path.cwd() / "trajectories"
    trajectories_dir.mkdir(exist_ok=True)

    logger.info("Running sweagent...")

    info: AgentInfo
    trajectory_steps: List[TrajectoryStep]

    start_time = time.time()
    info, trajectory_steps = agent.run(
        setup_args={"issue": getattr(env, "query", None), "files": [], "test_files": [], "tests": []},
        env=env,
        observation=observation,
        traj_dir=trajectories_dir,
        return_type="info_trajectory",
    )
    duration_s = time.time() - start_time

    if not (info["exit_status"] == "submitted" and info.get("submission") is not None):
        raise ValueError(f"SWE-agent failed to submit. Ran for {duration_s:.2f}s. Info: {info}")

    readable_info = {
        k: (v if k not in ["edited_files30", "submission", "edited_files50"] else f"{v[:100]}...")
        for k, v in info.items()
    }
    logger.info(f"Finished running sweagent, ran for {duration_s:.2f}s. Received info: {readable_info}")
    return IssueSolution(
        patch=info["submission"],
        model_stats=MinerModelStats.model_validate(
            info["model_stats"] | dict(duration_s=duration_s)
        )
    )