import asyncio
import discord
from discord.ext import commands
import swannybottokens
from help_cog import help_cog
from streamer_cog import streamer_cog
from special_cog import special_cog
from video_cog import video_cog
# from rep_cog import rep_cog
from twitterfixer_cog import twitterfixer_cog
from music_cog import MusicCog
import database
import wavelink


class Swannybot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.presences = True
        intents.members = True
        super().__init__(
        command_prefix=commands.when_mentioned_or('!'),
        description="SwannyBot",
        intents=intents,
        help_command = None
        )

    async def on_ready(self):
        discordPresence = discord.Game("all your faves with !p")
        await self.change_presence(activity=discordPresence)
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('Bot is ready!')
    async def setup_hook(self) -> None:
        nodes = [wavelink.Node(uri="http://docker:2333", password=swannybottokens.WavelinkPassword,
                               inactive_player_timeout=600)]
        # cache_capacity is EXPERIMENTAL. Turn it off by passing None
        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=100)
        database.dbhandler()
        await self.load_extension("music_cog")
        await self.load_extension("twitterfixer_cog")
        await self.load_extension("video_cog")
        await self.load_extension("help_cog")
        await self.load_extension("streamer_cog")
        await self.load_extension("special_cog")

swannybot :Swannybot= Swannybot()
async def main():
    async with swannybot:
        await swannybot.start(swannybottokens.discord_api_key)

asyncio.run(main())
