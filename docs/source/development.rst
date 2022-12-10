
Setting Up the Environment:
***********************************************************************
If you do not have a TACC account, follow the instructions on `SHADE AIE's onboarding page <https://www.shade-aie.org/learning-center/>`_. Once you have a TACC account, you can follow these directions to set up your environment.

1. SSH into a TACC server by substituting "uname" with your TACC User ID and running one of the following commands:

.. code-block:: bash

    ssh uname@frontera.tacc.utexas.edu
    ssh uname@ls6.tacc.utexas.edu

2. Clone the repository

.. code-block:: bash

    git clone https://github.com/ALLAN-DIP/baseline_bots.git
    cd baseline_bots/

3. Create a conda environment:

.. code-block:: bash

    conda create -n "shade" python==3.7
    conda activate shade

4. Install the dependencies:

.. code-block:: bash

    pip install -r requirements.txt
    pip install -e .

6. Add the path to the diplomacy_research repository (by replacing "uname" again and) running the following. It is also suggested to add these lines to .bashrc so you don't need to run it every time you log on.

.. code-block:: bash

    export WORKING_DIR=/home1/09102/uname/research/WORKING_DIR/
    export PYTHONPATH=$PYTHON-PATH:/home1/09102/uname/research/
    module load tacc-singularity

8. Connect github account

To connect your account, first, generate a Personal Access Token in Developer Settings on Github. Then, replace "token" with the personal token you generated and run the following in the baseline_bots repo:

.. code-block:: bash

    git remote set-url origin https://token@github.com/ALLAN-DIP/baseline_bots.git


9. Install the dependencies for diplomacy_research

.. code-block:: bash

    cd ~/research
    pip install -r requirements.txt 

Done! In the baseline_bots directory, you should now be able to run:

.. code-block:: bash

    pytest tests

Every time you log on to TACC, run the following command:

.. code-block:: bash

    idev -m 120

Using VSCode
***********************************************************************
1. Install the Remote-SSH extension on VSCode.
2. Open the Command Palette (Ctrl+Shift+P) and run the Remote-SSH: Connect to Host command.
3. Enter the ssh command to access the server (e.g. ssh kkahadze@frontera.tacc.utexas.edu).
4. When it asks you which config file to use, select the one in the .ssh folder in your home directory on your local system.

Modifying Documentation
***********************************************************************

After changing the documentation, you can build the documentation by running:

.. code-block:: bash

    sphinx-build -b html docs/source docs/build/html

Open the resultant html file in your browser to view the documentation.

.. code-block:: bash

    open docs/build/html/index.html

The 'sphinx-autobuild package can also be installed to automatically rebuild the documentation when a file is changed.'

.. code-block:: bash

    pip install sphinx-autobuild

Then, run:

.. code-block:: bash

    sphinx-autobuild docs/source docs/build/html


Running Tests
**********************************************************************************************************************************************
The following runs all tests in the tests directory. Look up pytest documentation to see 
how to run tests individually.

.. code-block:: bash

    pytest tests/

Pushing Code
************************************************

1. When beginning a new feature, checkout into a new branch
2. Use conventional commits
3. Always run the Makefile before pushing (it performs code styling)

More information about the CI practices can be found `here <https://www.youtube.com/watch?v=sw3v4Snopjc>`_.


How To Run Bots
****************************************************************************************************************

Check the `Google Doc <https://docs.google.com/document/d/1TTHKx09io3pWXqcH7FexeDOvCN_-HqgUp5WQyx7rBbk/edit?usp=sharing>`_ here for instructions on how to connect the bot to a TACC game and how to run them locally

General Tips
*****************************************************

- Adding the following line to .bashrc will activate your shade environment on login.

.. code-block:: bash

    conda activate shade

- If using VSCode, run the following command to remove the prompt command that is added by default:

.. code-block:: bash

    unset PROMPT_COMMAND 