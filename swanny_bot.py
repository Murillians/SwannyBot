import asyncio
import os

import discord
from discord.ext import commands

import swannybottokens
import requests
from help_cog import help_cog
from music_cog import music_cog
from streamer_cog import streamer_cog
from special_cog import special_cog
from video_cog import video_cog
#from rep_cog import rep_cog
import logging
import database
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

intents = discord.Intents.default()
intents.message_content = True
intents.presences=True
intents.members = True
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('!'),
    description="SwannyBot",
    intents=intents
)
@bot.event
async def on_ready():
    discordPresence = discord.Game("all your faves with !p")
    await bot.change_presence(activity=discordPresence)
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('Bot is ready!')

async def setup(bot):
    bot.remove_command("help")
    database.dbhandler()
    await bot.add_cog(help_cog(bot))
    await bot.add_cog(music_cog(bot))
    await bot.add_cog(streamer_cog(bot))
    await bot.add_cog(special_cog(bot))
    await bot.add_cog(video_cog(bot))
    await bot.add_cog(rep_cog(bot))
async def main():
    async with bot:
    #startup_check()
    #client = discord.Client(intents=discord.Intents.default())
        await setup(bot)
        await bot.start(swannybottokens.discord_api_key)

asyncio.run(main())
