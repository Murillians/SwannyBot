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
from rep_cog import rep_cog
import logging
import database
from twitterfixer_cog import twitterfixer_cog

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
    await bot.add_cog(twitterfixer_cog(bot))
async def main():
    async with bot:
    #client = discord.Client(intents=discord.Intents.default())
        await setup(bot)
        await bot.start(swannybottokens.discord_api_key)

asyncio.run(main())
