# Allan_Dip_Bot

Containerization code referenced from [SHADE-AI/diplomacy-playground](https://github.com/SHADE-AI/diplomacy-playground)

This is a docker implementation of ALLAN team's bots. The model parameters are embedded and the TF model server is run within the container along with a python script to instantiate the bot and facilitate game play.

Build:

```shell
docker pull allanumd/allan_bots:base-latest
docker build --target allan_dip_bot --tag allan_dip_bot --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from allanumd/allan_bots:base-latest .
```

Usage:

```shell
$ docker run -it allan_dip_bot --help
--host 		HOST [default localhost]
--port 		PORT [default 8432]
--game_id 	GAME_ID
--power		POWER
--bot_type  BOT_TYPE [default TransparentBot]
--outdir    OUT_DIR

#connect to remote game engine
$ docker run -it allan_dip_bot --game_id test_game --host shade.tacc.utexas.edu --power TURKEY
$
```
