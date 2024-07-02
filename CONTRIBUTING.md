# CONTRIBUTING

The `BaselineBot` class contains many utility methods that are useful for bots in general. All one needs to do is subclass `BaselineBot` and implement the abstract methods. There are some methods left entirely empty to serve as places to implement "hooks", while others you need to implement entirely from scratch. There is a method to use for the general game flow, but that can also be overwritten if needed.

Once you've created your own bot, you need to manually add it to `__init__.py` so it can be exported. All bots should be imported from `chiron_utils.bots` instead of their individual modules to make imports less verbose and to make refactoring more self-contained. The bot class also needs to be added to the list at the top of `scripts/run_bot.py` so it can be called as an argument.

If there are dependencies that are not purely Python, you will likely need to make some changes to the `Dockerfile` so the bot can be built. Some refactoring might be needed, and if the changes are large, it might be worth making separate targets for specific bots.

There should also be some documentation in the README on how to build each bot and the basics of how it works.

I (Alex) will have to make some changes to the bot runner scripts to pass in different types of bots for each power. That can be a relatively simple list with a default value, though. Also, I should probably move the list and the default bot class to `bots/__init__.py` to add more encapsulation and keep all general logic in a single place.

If your code base is particularly complex (e.g., CICERO), you should import `chiron_utils`` as a package. Otherwise, the bot should be developed right in this repository. Keeping as much as possible in a single place will make refactoring easier.

You generally should not be interfacing directly with game communications yourself and instead should be doing all such interactions through methods in `BaselineBot`. This will allow us to make changes to the _Diplomacy_ engine without individual bots needing to be changed.

I (Alex) will require all code meets the various standards set for the repository, which will involve code review. It is useful to add tests as well. They don't need to be comprehensive, but they should at least be a 1v1 against a `RandomProposalBot` to catch any obvious crashes.

If you want to share code between an advisor and a player, it's up to your how you structure it. You can factor out code into functions, or you can make a class your advisor and player both inherit from. It's up to you. Regardless, you _do_ need to declare the `bot_type` field as either `"advisor"` or `"player"`. These will become enums in the near future.

Feel free to create utilities and utility classes as needed. If something would be useful to reuse, then we should design it modularly so it can be used in multiple players. In addition, model training scripts and other files should all be stored in the repository to make them easy to find.

Models and other large files should be publicly accessible in some way, likely hosted on the Docker Hub (or GHCR), Hugging Face Hub, or both to make builds easier.
