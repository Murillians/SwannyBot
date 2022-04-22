from discord.ext import commands

import swannybottokens
from help_cog import help_cog
from music_cog import music_cog
from streamer_cog import streamer_cog
bot = commands.Bot(command_prefix="!")
bot.remove_command("help")
bot.add_cog(help_cog(bot))
bot.add_cog(music_cog(bot))
bot.add_cog(streamer_cog(bot))
bot.run(swannybottokens.discord_api_key)
