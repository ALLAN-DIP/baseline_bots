"""Generates file to run a game with Slurm's `sbatch`."""
import argparse
import datetime
import json
from pathlib import Path
from shlex import quote

from chiron_utils.utils import POWER_NAMES_DICT

REPO_DIR = Path(__file__).resolve().parent.parent.parent.parent

DEFAULT_HOST = "shade.tacc.utexas.edu"


def main() -> None:
    """Generate file to run with `sbatch`."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config_file",
        type=Path,
        help="Path to JSON file with game configurations",
    )
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
    config_file: Path = args.config_file
    host: str = args.host
    output_dir: Path = args.output_dir.resolve()

    games = json.loads(config_file.read_text())

    for game in games:
        # Create game with specified ID
        game_id = game["id"]
        # Time added for disambiguation across runs
        now = datetime.datetime.now(datetime.timezone.utc)
        game_id = f"{game_id}_{now.strftime('%Y_%m_%d_%H_%M_%S_%f')}"

        log_dir = output_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        data_dir = output_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        run_cmds = []
        powers = sorted(POWER_NAMES_DICT.values())
        for cuda_num, power in enumerate(powers):
            script_path = REPO_DIR / "scripts" / "run_antony.sh"
            log_file = str(log_dir / f"{power}.txt")
            agent = game["agents"].get(power)
            if agent is None or "agent_params" not in agent:
                agent_params = ""
            else:
                agent_params = agent["agent_params"] + " "
            run_cmds.append(
                f"bash {quote(str(script_path))} {quote(game_id)} {quote(host)} {power} "
                f"{quote(str(output_dir))} {cuda_num} {agent_params}|& tee {quote(log_file)}"
            )
        print("Commands:\n" + "\n".join(f"- {c!r}" for c in run_cmds))
        command_file = data_dir / f"config_{game_id}.json"
        command_json = {
            "commands": run_cmds,
            "game_id": game_id,
            "host": host,
            "data_dir": str(data_dir),
        }

        command_file.write_text(json.dumps(command_json, ensure_ascii=False, indent=2))
        print(f"Wrote command file to:\n{quote(str(command_file))}")


if __name__ == "__main__":
    main()
