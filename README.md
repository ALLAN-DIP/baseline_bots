# Baselines Bots

## Install

Diplomacy lib and DAIDE parser

```
pip install diplomacy
pip install git+https://github.com/trigaten/DAIDE
```

## Bots

[x] means it has been updated to Kartik's new style

This is a collection of simple baseline bots

The bot parent-child relationships are as follow:

* baseline_bot - Abstract Base Class

    * loyal_bot - accepts an alliance and follows allies' orders (Joy #6)

    * pushover_bot - executes whatever orders the last message told it to (Joy #5)

    * random_proposer_bot - randomly proposes moves to other bots [x]

        * random_allier_proposer_bot - first sends alliance proposals then randomly proposes moves to other bots

    * random_honest_order_accepter_bot - randomly accepts proposed orders and messages the proposers whose moves it accepted (Joy #4)

    * random_honest_bot - executes random orders and messages all other bots the orders it executed 


### Using diplomacy_research

```python

idev -m 60
export WORKING_DIR=~/dipnet_press/WORKING_DIR/
module load tacc-singularity
# activate conda environment
conda activate diplomacy
# add path to diplomacy_research to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:/home1/08764/trigaten/research/diplomacy_research


```