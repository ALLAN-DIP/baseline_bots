# Baselines Bots

This is a collection of simple baseline bots

The bot parent-child relationships are as follow:

* baseline_bot - Abstract Base Class

    * loyal_bot - accepts an alliance and follows allies' orders (Joy #6)

    * pushover_bot - executes whatever orders the last message told it to (Joy #5)

    * random_proposer_bot - randomly proposes moves to other bots

        * random_allier_proposer_bot - first sends alliance proposals then randomly proposes moves to other bots

    * random_honest_order_accepter_bot - randomly accepts proposed orders and messages the proposers whose moves it accepted (Joy #4)

    * random_honest_bot - executes random orders and messages all other bots the orders it executed 
