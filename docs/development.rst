Development 
================

Setting up your development environment:
***********************************************************************

1. Create a conda environment:

.. code-block:: python

    conda create -n "shade" python==3.7
    conda activate shade

2. Install the dependencies:

.. code-block:: python

    pip install -r requirements.txt

3. Install the package in development mode:

.. code-block:: python

    pip install -e .

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

Development on TACC and using diplomacy_research:
**********************************************************************************************************************************************

.. code-block:: bash

    idev -m 60
    export WORKING_DIR=~/dipnet_press/WORKING_DIR/
    module load tacc-singularity
    # activate conda environment
    conda activate shade
    # add path to diplomacy_research to PYTHONPATH--your path should be different
    export PYTHONPATH=$PYTHONPATH:/home1/08764/trigaten/research/diplomacy_research
