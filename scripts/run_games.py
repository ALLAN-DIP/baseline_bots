import argparse
import asyncio
import datetime
import getpass
import json
from pathlib import Path
from shlex import quote
import socket
from typing import List, Optional, Sequence

from create_game import create_game
from download_game import download_game

from baseline_bots.utils import POWER_NAMES_DICT

REPO_DIR = Path(__file__).resolve().parent.parent

APPTAINER = "apptainer"
DOCKER = "docker"
SINGULARITY = "singularity"

IS_ON_CARC = socket.getfqdn().endswith(".usc.edu")
IS_ON_TACC = socket.getfqdn().endswith(".tacc.utexas.edu")

if IS_ON_CARC:
    DEFAULT_RUNNER = SINGULARITY
elif IS_ON_TACC:
    DEFAULT_RUNNER = APPTAINER
else:
    DEFAULT_RUNNER = DOCKER

DEFAULT_HOST = "shade.tacc.utexas.edu"


async def run_cmd(cmd: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        "/usr/bin/env",
        *("bash", "-c", cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8")


async def run_all_cmds(cmds: Sequence[str], *, delay_seconds: Optional[int] = None) -> List[str]:
    coroutines = []
    for cmd in cmds:
        coroutines.append(run_cmd(cmd))
        if delay_seconds is not None:
            await asyncio.sleep(delay_seconds)
    return await asyncio.gather(*coroutines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runner",
        default=DEFAULT_RUNNER,
        type=str,
        choices=(APPTAINER, DOCKER, SINGULARITY),
        help=f"Container runtime. Defaults to {SINGULARITY!r} on CARC, {APPTAINER!r} on TACC, and "
        f"{DOCKER!r} everywhere else. (current default: %(default)s)",
    )
    parser.add_argument(
        "--game-id",
        help="Game ID. If one is not provided, then one will be generated automatically. "
        "Defaults to `$USER_$(date -u +'%%Y_%%m_%%d_%%H_%%M_%%S_%%f')`.",
    )
    parser.add_argument(
        "--agent",
        default=None if IS_ON_CARC or IS_ON_TACC else "achilles",
        type=str,
        help="Bot to run. (current default: %(default)s)",
    )
    parser.add_argument("--bot_args", type=str, help="Extra arguments to pass to bot.")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        type=str,
        help="Server hostname. (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default=REPO_DIR,
        type=Path,
        help="Directory to store run output. (default: %(default)s)",
    )
    args = parser.parse_args()
    runner: str = args.runner
    game_id: Optional[str] = args.game_id
    agent: str = args.agent
    host: str = args.host
    output_dir: Path = args.output_dir
    extra_bot_args: Optional[str] = args.bot_args
    if runner == APPTAINER:  # For TACC
        # Flags based on following docs:
        # - https://apptainer.org/docs/user/1.1/cli/apptainer_run.html
        # - https://apptainer.org/docs/user/1.1/docker_and_oci.html#docker-like-compat-flag
        runner_command = (
            "apptainer run --cleanenv --ipc --no-eval --no-home --no-init --no-umask --pid"
        )
    elif runner == DOCKER:  # For local development
        runner_command = "docker run --rm"
    elif runner == SINGULARITY:  # For CARC
        # Flags based on following docs:
        # - https://docs.sylabs.io/guides/3.11/user-guide/cli/singularity_run.html
        # - https://docs.sylabs.io/guides/3.11/user-guide/singularity_and_docker.html#docker-like-compat-flag
        runner_command = "singularity run --compat"
    else:
        # Should never happen
        raise ValueError(f"Provided container runtime {runner!r} not recognized.")
    runner_command += " --env NO_COLOR=1"
    if game_id is None:
        user = getpass.getuser()
        now = datetime.datetime.now(datetime.timezone.utc)
        game_id = f"{user}_{now.strftime('%Y_%m_%d_%H_%M_%S_%f')}"
        create_game_data = asyncio.run(create_game(game_id, hostname=host))
        print(json.dumps(create_game_data, ensure_ascii=False, indent=2))
    bot_args = ""
    if extra_bot_args is not None:
        bot_args += f" {extra_bot_args}"
    log_dir = output_dir / "logs" / game_id
    log_dir.mkdir(parents=True, exist_ok=True)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    powers = sorted(POWER_NAMES_DICT.values())
    run_cmds = []
    for power in powers:
        if runner == DOCKER:
            runner_command += f" --name {power}-{game_id}"
        # `localhost` doesn't work when running an agent with Docker Desktop
        host_from_container = "host.docker.internal" if host == "localhost" else host
        log_file = str(log_dir / f"{power}.txt")
        run_cmds.append(
            f"{runner_command} {quote(agent)} --host {quote(host_from_container)} "
            f"--game_id {quote(game_id)} --power {power} {bot_args} |& tee {quote(log_file)}"
        )
    print(run_cmds)

    results = asyncio.run(run_all_cmds(run_cmds, delay_seconds=4))
    run_output = {
        power: {"command": cmd, "console_output": result}
        for power, cmd, result in zip(powers, run_cmds, results)
    }
    game_record = asyncio.run(download_game(game_id, hostname=host))
    output = {"run_output": run_output, "game_record": game_record}
    output_file = data_dir / f"{game_id}.json"
    with open(output_file, "w") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()
