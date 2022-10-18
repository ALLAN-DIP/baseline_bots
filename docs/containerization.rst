Containerization 
================

Containerization code referenced from SHADE-AI/diplomacy-playground

This is a docker implementation of ALLAN team's bots. 
The model parameters are embedded and the TF model server is run within the container along with a python script to instantiate the bot and facilitate game play.

Building the container
***********************************************************************

1. Go to subdirectory:

.. code-block:: python

    cd containers/allan_dip_bot/

2. Download and unzip the model file:

.. code-block:: bash

    $ wget https://f002.backblazeb2.com/file/ppaquette-public/benchmarks/neurips2019-sl_model.zip
	$ mkdir bot_neurips2019-sl_model
	$ unzip neurips2019-sl_model.zip -d bot_neurips2019-sl_model/

3. Build the docker container with the tag to be used while pushing it to DockerHub:

.. code-block:: bash

    $ docker build -t uname/allan_dip_bot .
	$ docker push uname/allan_dip_bot

Usage
************************************************

.. code-block:: bash

    $ docker run -it allan_dip_bot --help
	--host 		HOST [default localhost]
	--port 		PORT [default 8432]
	--game_id 	GAME_ID
	--power		POWER
	--bot_type  BOT_TYPE [default TransparentBot]
	--outdir    OUT_DIR

	#connect to remote game engine
	$ docker run uname/allan_dip_bot --game_id test_game --host shade.tacc.utexas.edu --power TURKEY
	$ singularity run uname/allan_dip_bot --game_id test_game --host shade.tacc.utexas.edu --power TURKEY