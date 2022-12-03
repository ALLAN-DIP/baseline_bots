
Setting up your development environment:
***********************************************************************
If you do not have a TACC account, follow the instructions on `SHADE AIE's onboarding page <https://www.shade-aie.org/learning-center/>`_.

Once you have a TACC account, you can follow these directions to set up your environment.

1. SSH into a TACC server by substituting "uname" with your TACC User ID

.. code-block:: bash
    ssh uname@ls6.tacc.utexas.edu

or 
.. code-block:: bash
    ssh uname@frontera.tacc.utexas.edu

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

6. Add the path to the diplomacy_research repository (replacing "uname" again) by running the following. It is also suggested to add these lines to .bashrc so you don't need to run it every time you log on.

.. code-block:: bash

    export WORKING_DIR=/home1/09102/uname/research/WORKING_DIR/
    export PYTHONPATH=$PYTHON-PATH:/home1/09102/uname/research/
    module load tacc-singularity

8. Connecting github account

To connect your account, first, generate a Personal Access Token in Developer Settings on Github

Then, replace "token" with the personal token you generated and run the following in the baseline_bots repo:

.. code-block:: bash
    git remote set-url origin https://token@github.com/ALLAN-DIP/baseline_bots.git


9. Install the dependencies for diplomacy_research

.. code-block:: bash
    cd ~/research
    pip install -r requirements.txt 

Done! In the baseline_bots directory, you should now be able to run:

.. code-block:: bash
    pytest tests

Every time you log on:
***********************************************************

Run:

.. code-bloc:: bash
    idev -m 120

Modifying documentation:
***********************************************************************

After changing the documentation, you can build the documentation by running:

.. code-block:: bash

    sphinx-build -b html docs/ docs/build/html

Open the resultant html file at docs/build/html/index.html 
in your browser to view the documentation.

Running tests:
**********************************************************************************************************************************************
The following runs all tests in the tests directory. Look up pytest documentation to see 
how to run tests individually.
.. code-block:: bash

    pytest tests/

Pushing code:
************************************************

1. When beginning a new feature, checkout into a new branch
2. Use conventional commits
3. Always run the Makefile before pushing (it performs code styling)

More information about the CI practices can be found `here <https://www.youtube.com/watch?v=sw3v4Snopjc>`_


How to run bots
****************************************************************************************************************

Check the `Google Doc <https://docs.google.com/document/d/1TTHKx09io3pWXqcH7FexeDOvCN_-HqgUp5WQyx7rBbk/edit?usp=sharing>`_ here for instructions on how to connect the bot to a TACC game and how to run them locally

General Tips:
*****************************************************

- Adding the following line to .bashrc will activate your shade environment on login.

.. code-block:: bash
    conda activate shade

- If using VSCode, run `unset PROMPT_COMMAND` in the terminal or add it to .bashrc
Otherwise, you may see a lot of `__vsc_prompt_cmd_original`