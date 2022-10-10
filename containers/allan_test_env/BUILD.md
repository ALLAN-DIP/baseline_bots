# Allan_Dip_Bot

Containerization code referenced from [SHADE-AI/diplomacy-playground](https://github.com/SHADE-AI/diplomacy-playground)

This is a docker implementation of ALLAN team's bots. The model parameters are embedded and the TF model server is run within the container along with a python script to instantiate the bot and facilitate game play. 

Build:
```shell
$ wget https://f002.backblazeb2.com/file/ppaquette-public/benchmarks/neurips2019-sl_model.zip
$ mkdir bot_neurips2019-sl_model
$ unzip neurips2019-sl_model.zip -d bot_neurips2019-sl_model/
$ docker build -t allan_test_env . 
```

Usage:
```shell
$ docker run -it allan_test_env --help
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

