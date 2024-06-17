# Running many ANTONY games

## Setup

These scripts need to be run in a Python environment with a recent version of `diplomacy` installed. They have only been tested with Python 3.7, the latest version that `diplomacy` officially supports.

`run_antony.sh`, which actually runs the ANTONY agent, requires a specific directory layout to work properly. The current directory needs a copy of the <https://github.com/ALLAN-DIP/diplomacy_cicero> repository cloned to a directory called `diplomacy_cicero` and with the desired branch checked out. In addition, it requires a directory named `cicero/` with the subdirectories `agents/`, `gpt2/`, and `models/`, as is currently done when running ANTONY elsewhere.

Before attempting to use the orchestrator, focus on getting `run_antony.sh` to run properly in an `srun` session. Use the same Slurm configuration as in `game_runner.sh` except with 1 GPU instead of 7.

## Usage

The workflow for this orchestration is unfortunately complex. Here are the steps to run games:

1. Create JSON config file (e.g., `config.json`) describing games to run
2. Run `generate_sbatch.py` to create command files for individual games

   ```bash
   python scripts/generate_sbatch.py config.json --output-dir output/
   ```

3. Run `game_runner.sh` with `sbatch` and a game command file as input

   ```bash
   USER_EMAIL=$USER@$(hostname | sed 's/.*\.\(.*\..*\)/\1/g')
   SLURM_SCRIPT=$(realpath scripts/game_runner.sh)
   COMMAND_FILE=$(realpath config_antony_template_2023_09_01_22_39_28_312128.json)
   sbatch --mail-user="$USER_EMAIL" "$SLURM_SCRIPT" "$COMMAND_FILE"
   ```

   These steps do not require any user intervention, but they are useful to know when debugging:

   1. `game_runner.sh` directly runs `run_game.py`. It only exists as a wrapper for running the Python script with Slurm.
   2. `run_game.py` sets up a single game, runs the provided commands, and saves results for that game.
   3. `run_antony.sh`, called by the generated commands, runs an ANTONY container.

Some of the file paths need to be changed to fit your specific setup. All commands must be run from same directory because the generated files contain hardcoded paths.

To run only a single game, define a single game in the configuration file and use the following definition for `COMMAND_FILE` in step 3 above:

```bash
COMMAND_FILE=$(python scripts/generate_sbatch.py config.json --output-dir output/ | tail -1)
```

## Limitations

Although there is a `stop_year` field defined in the JSON format, it does not currently work as Alex is unaware of how to make ANTONY stop after a particular point. The games will keep running until they are finished.

For simplicity, environment variables cannot be passed to ANTONY at this time. This was done as a simplification to save time, and Alex can add the functionality if needed.

## Data formats

Here is an example of the JSON format for step 1:

```json
[
  {
    "id": "antony_game1",
    "agents": {
      "AUSTRIA": {
        "agent_params": "--model baseline"
      },
      "ENGLAND": {
        "agent_params": "--model silent"
      }
    },
    "stop_year": 1905
  },
  {
    "id": "antony_game2",
    "agents": {
      "AUSTRIA": {
        "agent_params": "--model silent"
      },
      "ENGLAND": {
        "agent_params": "--model baseline"
      }
    },
    "stop_year": 1908
  }
]
```

The above configuration describes two games. Only 2 countries are listed for each game for brevity, but all 7 should be defined. If a country is not included, then the agent will run without any extra parameters being added.

See `config.json` for a minimal configuration and `config_template.json` for a slightly more complex one.

Here is an example from Alex's testing of the JSON generated for a single game as part of step 2:

```json
{
  "commands": [
    "bash /project/jonmay_231/ahedges/baseline_bots/scripts/run_antony.sh ahedges_antony_test_2023_09_12_19_33_49_856274 shade.tacc.utexas.edu AUSTRIA /project/jonmay_231/ahedges/output_2023_09_12_19_33_47 0 |& tee /project/jonmay_231/ahedges/output_2023_09_12_19_33_47/logs/AUSTRIA.txt",
    "bash /project/jonmay_231/ahedges/baseline_bots/scripts/run_antony.sh ahedges_antony_test_2023_09_12_19_33_49_856274 shade.tacc.utexas.edu ENGLAND /project/jonmay_231/ahedges/output_2023_09_12_19_33_47 1 |& tee /project/jonmay_231/ahedges/output_2023_09_12_19_33_47/logs/ENGLAND.txt",
    "bash /project/jonmay_231/ahedges/baseline_bots/scripts/run_antony.sh ahedges_antony_test_2023_09_12_19_33_49_856274 shade.tacc.utexas.edu FRANCE /project/jonmay_231/ahedges/output_2023_09_12_19_33_47 2 |& tee /project/jonmay_231/ahedges/output_2023_09_12_19_33_47/logs/FRANCE.txt",
    "bash /project/jonmay_231/ahedges/baseline_bots/scripts/run_antony.sh ahedges_antony_test_2023_09_12_19_33_49_856274 shade.tacc.utexas.edu GERMANY /project/jonmay_231/ahedges/output_2023_09_12_19_33_47 3 |& tee /project/jonmay_231/ahedges/output_2023_09_12_19_33_47/logs/GERMANY.txt",
    "bash /project/jonmay_231/ahedges/baseline_bots/scripts/run_antony.sh ahedges_antony_test_2023_09_12_19_33_49_856274 shade.tacc.utexas.edu ITALY /project/jonmay_231/ahedges/output_2023_09_12_19_33_47 4 |& tee /project/jonmay_231/ahedges/output_2023_09_12_19_33_47/logs/ITALY.txt",
    "bash /project/jonmay_231/ahedges/baseline_bots/scripts/run_antony.sh ahedges_antony_test_2023_09_12_19_33_49_856274 shade.tacc.utexas.edu RUSSIA /project/jonmay_231/ahedges/output_2023_09_12_19_33_47 5 |& tee /project/jonmay_231/ahedges/output_2023_09_12_19_33_47/logs/RUSSIA.txt",
    "bash /project/jonmay_231/ahedges/baseline_bots/scripts/run_antony.sh ahedges_antony_test_2023_09_12_19_33_49_856274 shade.tacc.utexas.edu TURKEY /project/jonmay_231/ahedges/output_2023_09_12_19_33_47 6 |& tee /project/jonmay_231/ahedges/output_2023_09_12_19_33_47/logs/TURKEY.txt"
  ],
  "game_id": "ahedges_antony_test_2023_09_12_19_33_49_856274",
  "host": "shade.tacc.utexas.edu",
  "data_dir": "/project/jonmay_231/ahedges/output_2023_09_12_19_33_47"
}
```
