import os

from discord.ext import commands

import swannybottokens
import requests
from help_cog import help_cog
from music_cog import music_cog
from streamer_cog import streamer_cog
from special_cog import special_cog
import logging

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix='!')

    async def on_ready(self):
        print('Bot is ready!')

def startup_check():
    #currently not working, fix downloading function
    # ensure we have lavalink jar
    if os.path.exists("/wavelink/lavalink.jar"):
        logging.info("Found wavelink.jar file, continuing")
        return
    else:
        lavalink_url = "https://github.com/freyacodes/Lavalink/releases/latest/assets/download/Lavalink.jar"
        response = requests.get(lavalink_url, allow_redirects=True)
        open("wavelink/lavalink.jar", "wb").write(response.content)
        os.system("java -jar wavelink/lavalink.jar")
        if os.path.exists("/wavelink/lavalink.jar"):
            return
        else:
            logging.fatal("Failed to automatically download lavalink jar, please manually download")
            exit()


#startup_check()
bot = Bot()
bot.remove_command("help")
bot.add_cog(help_cog(bot))
bot.add_cog(music_cog(bot))
bot.add_cog(streamer_cog(bot))
bot.add_cog(special_cog(bot))
bot.run(swannybottokens.discord_api_key)
