"""Run a single game on CARC."""

import argparse
import asyncio
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Sequence, Tuple

from chiron_utils.game_utils import create_game, download_game
from chiron_utils.utils import POWER_NAMES_DICT

REPO_DIR = Path(__file__).resolve().parent.parent.parent.parent


async def run_cmd(cmd: str) -> Dict[str, Any]:
    """Run a shell command, capturing all output in the process.

    Args:
        cmd: Command to run.

    Returns:
        Command's console output (both stdout and stderr) and exit code.
    """
    proc = await asyncio.create_subprocess_exec(
        "/usr/bin/env",
        *("bash", "-c", cmd),
        # Write stdout and stderr as a single stream
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    exit_code = proc.returncode
    return {
        "stdout": stdout.decode("utf-8"),
        "exit_code": exit_code,
    }


async def run_all_cmds(
    cmds: Sequence[str], *, delay_seconds: Optional[int] = None
) -> Tuple[Dict[str, Any]]:
    """Runs multiple commands, capturing their output.

    Args:
        cmds: List of shell commands to run.
        delay_seconds: Number of seconds to wait between running each command.

    Returns:
        Separate output for each command.
    """
    coroutines = []
    for cmd in cmds:
        coroutines.append(run_cmd(cmd))
        if delay_seconds is not None:
            await asyncio.sleep(delay_seconds)
    return await asyncio.gather(*coroutines)  # type: ignore[no-any-return]


def main() -> None:
    """Runs commands from provided file and stores command output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command_file",
        type=Path,
        help="Path to JSON file with information to run a single game.",
    )
    args = parser.parse_args()
    command_file: Path = args.command_file

    command_json = json.loads(command_file.read_text())
    run_cmds = command_json["commands"]
    game_id = command_json["game_id"]
    host = command_json["host"]
    data_dir = Path(command_json["data_dir"])
    data_dir.mkdir(parents=True, exist_ok=True)

    create_game_data = asyncio.run(create_game(game_id, hostname=host))
    print(json.dumps(create_game_data, ensure_ascii=False, indent=2))

    results = asyncio.run(run_all_cmds(run_cmds, delay_seconds=4))
    powers = sorted(POWER_NAMES_DICT.values())
    run_output = {}
    for power, cmd, result in zip(powers, run_cmds, results):
        run_output[power] = {
            "command": cmd,
            "stdout": result["stdout"],
            "exit_code": result["exit_code"],
        }
    game_record = asyncio.run(download_game(game_id, hostname=host))
    output = {"run_output": run_output, "game_record": game_record}
    output_file = data_dir / f"game_{game_id}.json"
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)
        file.write("\n")

    # Exit code of child processes can be negative:
    # https://docs.python.org/3.7/library/asyncio-subprocess.html#asyncio.asyncio.subprocess.Process.returncode
    sub_exit_codes = [result["exit_code"] for result in results]
    if max(sub_exit_codes) > 0:
        exit_code = max(sub_exit_codes)
    elif min(sub_exit_codes) < 0:
        exit_code = min(sub_exit_codes)
    else:
        exit_code = 0
    print(f"Exit code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
