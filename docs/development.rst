Development 
================

Here are some instructions for setting up your development environment:
***********************************************************************

1. Create a conda environment:

.. code::python

    conda create -n "shade" python==3.7
    conda activate shade

2. Install the dependencies:

.. code::python

    pip install -r requirements.txt

3. Install the package in development mode:

.. code::python

    pip install -e .

Here are some instructions for modifying documentation:
***********************************************************************

After changing the documentation, you can build the documentation by running:

.. code::bash

    sphinx-build -b html docs/ docs/build/html

Open the resultant html file at docs/build/html/index.html 
in your browser to view the documentation.