import asyncio
import logging
import datetime
import discord
from discord.ext import commands
import swannybottokens
import wavelink


# TODO: Remove t from all commands and aliases when finished.
# Idle Bot Timeout
# TODO: Remove this function when 3.2.0 releases and enable on_wavelink_inactive_player at bottom.
# TODO: Then add inactive_timeout time to node parameter in swanny_bot.py
async def timeout(player: wavelink.Player):
    await asyncio.sleep(600)
    if player.playing is not True:
        await player.disconnect()

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f'Node <{node}> is ready')

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
                # track = await wavelink_player.queue.get_wait()
                await wavelink_player.play(tracks[0])
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
        if not await wavelink_player.pause(True):
            await wavelink_player.pause(True)
        else:
            await wavelink_player.pause(False)

    # Resume Function
    @commands.command(name="tresume", aliases=["r"])
    async def resume(self, ctx, *args):
        wavelink_player = self.get_current_player(ctx)
        if wavelink_player.pause(True):
            await wavelink_player.pause(False)

    # TODO: Skip function needs fixing, currently skips all tracks in a queue, not just one.
    # Skip Function
    @commands.command(name="tskip", aliases=["s"])
    async def skip(self, ctx, *args):
        wavelink_player = self.get_current_player(ctx)
        if wavelink_player is not None and wavelink_player.playing:
            await wavelink_player.skip()
            await ctx.message.add_reaction("\u2705")

    # Queue Function
    @commands.command(name="tqueue", aliases=["tq"])
    async def queue(self, ctx):
        wavelink_player = self.get_current_player(ctx)
        current_queue = wavelink_player.queue
        autoplay_queue = wavelink_player.auto_queue
        return_value = "Up Next: \n\n"
        for i in range(1, len(wavelink_player.queue)):
            if i > 4:
                break
            return_value += current_queue[i].title + '\n'
        if len(autoplay_queue) != 0:
            return_value += "\nAuto Play Queue: \n\n"
            for i in range(0, len(autoplay_queue)):
                if i > 4:
                    break
                return_value += autoplay_queue[i].title + ' - ' + autoplay_queue[i].author[0] + '\n'
        if return_value != "Up Next: \n\n" or wavelink_player.playing:
            await ctx.send(embed=discord.Embed(
                color=0x698BE6,
                title=wavelink_player.current.title,
                description=wavelink_player.current.author).set_author(
                name="Now Playing",
                icon_url="https://i.imgur.com/GGoPoWM.png").set_footer(
                text=return_value)
            )
        else:
            await ctx.send("No music in the queue.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        if player.autoplay is True:
            return
        current_queue = payload.player.queue
        if len(current_queue) >= 1:
            next_song = await current_queue.get_wait()
            await player.play(next_song)
        else:
            await timeout(player)

    # @commands.Cog.listener()
    # async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
    #     await player.channel.send(f"The player has been inactive for `{player.inactive_timeout}` seconds. Goodbye!")
    #     await player.disconnect()

    # Get Helper, helps generate an instance of the bot whenever a command is called.
    # Designed for usage in multiple discord guilds.
    def get_current_player(self, ctx: commands.Context):
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)
        return player

    async def cog_load(self):
        print(f"{self.__class__.__name__} loaded!")


async def setup(bot):
    # finally, adding the cog to the bot
    await bot.add_cog(MusicCog(bot=bot))
