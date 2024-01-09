import asyncio
import logging
import datetime
import discord
from discord.ext import commands
import swannybottokens
import wavelink


# Idle Bot Timeout
async def timeout(player):
    await asyncio.sleep(600)
    if player.is_playing() is not True:
        await player.disconnect()


class MusicCog(commands.Cog):
    node = wavelink.Node(uri='127.0.0.1:2333',
                         password=swannybottokens.WavelinkPassword)

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self.connect_nodes())

    # Ready Function
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f'Node <{node}> is ready')

    # TODO: I think we need to connect the LavaSrc plugin here?
    async def connect_nodes(self) -> None:
        await self.bot.wait_until_ready()
        await wavelink.Pool.connect(client=self.bot, nodes=[self.node])

    # Connect Function Helper
    @commands.command()
    async def connect(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        try:
            channel = channel or ctx.author.voice.channel
        except AttributeError:
            return await ctx.send("Connect to a voice channel!")
        vc: wavelink.Player = await channel.connect(cls=wavelink.Player)  # type: ignore
        return vc

    # Play Function
    # Should not handle any technical information about playing, only discord channel facing play.
    @commands.command(name="tplay", aliases=["tp"])
    async def play(self, ctx: commands.Context, *, query: str):
        wavelink_player = self.get_current_player(ctx)

        # Try to get the current player. If not found, connect.
        if wavelink_player is None:
            wavelink_player: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        # Begin search for a playable to add to queue.
        # Declare message that gets printed in reply to user play request.
        discord_message = None
        tracks: wavelink.Search = await wavelink.Playable.search(query)
        if tracks is not None:
            discord_message = tracks

        # Send an error if none of the parses could find a song.
        if tracks is None:
            await ctx.reply("Sorry, I could not find your song!")
            return
        try:
            if wavelink_player.playing is False:
                track = await wavelink_player.queue.get_wait()
                await wavelink_player.play(track)
        except Exception as e:
            print(e)
            pass
        if isinstance(tracks, wavelink.Playlist):
            # tracks is a playlist...
            added: int = await wavelink_player.queue.put_wait(tracks)
            await ctx.send(f"Added the playlist **`{tracks.name}`** ({added} songs) to the queue.")
        else:
            track: wavelink.Playable = tracks[0]
            await wavelink_player.queue.put_wait(track)
            await ctx.send(f"Added **`{track}`** to the queue.")

    # Pause Function
    @commands.command(name="tpause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        wavelink_player = self.get_current_player(ctx)
        if not wavelink_player.pause(True):
            await wavelink_player.pause(True)
        else:
            await wavelink_player.pause(False)

    # Get Helper, helps generate an instance of the bot whenever a command is called.
    # Designed for usage in multiple discord guilds.
    def get_current_player(self, ctx: commands.Context):
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)
        return player
