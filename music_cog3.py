import asyncio
import logging
import datetime
import discord
from discord.ext import commands
import swannybottokens
import wavelink


# TODO: Remove t from all commands and aliases when finished.
# Idle Bot Timeout
# TODO: Remove this timeout function when 3.2.0 releases and enable on_wavelink_inactive_player at bottom.
# TODO: Then add inactive_timeout time to node parameter in swanny_bot.py
# TODO: Change timeout back to 600 seconds
# TODO: Add mario bye bye sound before disconnecting to timeout :)
# https://www.youtube.com/watch?v=Sx3nXA23jjo
async def timeout(player: wavelink.Player):
    await asyncio.sleep(15)
    if player.playing is not True:
        await player.disconnect()



class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f"Node {payload.node!r} is ready!")

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

        # Autoplay Function that runs the queue. Setting the mode to partial will run the queue without recc's.
        if not wavelink_player.playing:
            wavelink_player.autoplay = wavelink.AutoPlayMode.partial

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

        # Determine the playable
        if isinstance(tracks, wavelink.Playlist):
            # tracks is a playlist...
            added: int = await wavelink_player.queue.put_wait(tracks)
            await ctx.send(f"Added the playlist **`{tracks.name}`** ({added} songs) to the queue.")
        else:
            track: wavelink.Playable = tracks[0]
            await wavelink_player.queue.put_wait(track)
            await ctx.send(f"Added **`{track}`** to the queue.")

        # Start the player if it is not playing
        try:
            if wavelink_player.playing is False:
                await wavelink_player.play(wavelink_player.queue.get())
        except Exception as e:
            print(e)
            pass

        # Delete invoked user message
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        if not hasattr(wavelink_player, "home"):
            wavelink_player.home = ctx.channel
        elif wavelink_player.home != ctx.channel:
            await ctx.send(
                f"You can only play songs in {wavelink_player.home.mention}, as the player has already started there.")
            return

    # Autoplay Toggle Function
    @commands.command(name="tautoplay", aliases=["tap"])
    async def autoplay(self, ctx: commands.Context):
        wavelink_player: wavelink.Player = self.get_current_player(ctx)
        if wavelink_player is None:
            wavelink_player: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)  # Type:ignore
        if wavelink_player.autoplay == wavelink.AutoPlayMode.partial:
            await ctx.reply("Okay, I will start looking for recommended tracks based on your queries!")
            wavelink_player.autoplay = wavelink.AutoPlayMode.enabled
        else:
            await ctx.reply("No problem, I will stop looking for recommended tracks!")
            wavelink_player.autoplay = wavelink.AutoPlayMode.partial

    # Command to add song to an established queue and play it next.
    # TODO: Need to find method to add song to top of queue.
    @commands.command(name="tplaynext", aliases=["tpn"])
    async def play_next(self, ctx: commands.Context, *, query: str):
        temp_ctx = ctx
        temp_query = query
        await self.play(temp_ctx, query=temp_query)
        wavelink_player = self.get_current_player(ctx)
        current_queue = wavelink_player.queue
        last_added = current_queue[-1]
        # No longer put_at_front method, can't insert into queue (class: Playable)

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

    # Skip Function
    @commands.command(name="tskip", aliases=["ts"])
    async def skip(self, ctx, *args):
        wavelink_player = self.get_current_player(ctx)
        if wavelink_player is not None and wavelink_player.playing:
            await wavelink_player.skip()
            await ctx.message.add_reaction("<:ThumbsUp:936340890086158356>")

    # Queue Function
    @commands.command(name="tqueue", aliases=["tq"])
    async def queue(self, ctx):
        wavelink_player = self.get_current_player(ctx)
        current_queue = wavelink_player.queue
        autoplay_queue = wavelink_player.auto_queue
        return_value = "Up Next: \n\n"
        try:
            for i in range(0, len(current_queue)):
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
                await ctx.send("Error 2: No music in the queue.")
        except Exception as e:
            print(e)
            await ctx.send("Error 3: No music in the queue.")
            pass

    # Shuffle Queue Function
    @commands.command(name="tshuffle", aliases=["tshuf"])
    async def shuffle(self, ctx):
        wavelink_player = self.get_current_player(ctx)
        current_queue = wavelink_player.queue
        autoplay_queue = wavelink_player.auto_queue
        if wavelink_player.playing:
            if len(current_queue) or len(autoplay_queue) != 0:
                current_queue.shuffle()
                autoplay_queue.shuffle()
                await ctx.send("The current queue was shuffled!")
        else:
            await ctx.send("No music in the queue!")

    # Clear Queue Function
    @commands.command(name="tclear", aliases=["tc", "tbin"])
    async def clear(self, ctx, *args):
        wavelink_player = self.get_current_player(ctx)
        if wavelink_player is not None and wavelink_player.playing:
            wavelink_player.queue.clear()
            await wavelink_player.stop()
        await ctx.send("Music queue cleared")

    # Leave Function
    @commands.command(name="tleave", aliases=["tdisconnect", "tl", "td"])
    async def leave(self, ctx):
        wavelink_player = self.get_current_player(ctx)
        wavelink_player.queue.clear()
        await wavelink_player.disconnect()

    # @commands.Cog.listener()
    # async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
    #     await player.channel.send(f"The player has been inactive for `{player.inactive_timeout}` seconds. Goodbye!")
    #     await player.disconnect()

    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            return

    @commands.Cog.listener()
    async def on_wavelink_track_end(self,payload: wavelink.TrackEndEventPayload):
        player = payload.player
        if not player.playing:
            await timeout(player)

    def get_current_player(self, ctx: commands.Context):
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)
        return player

    # Get Helper, helps generate an instance of the bot whenever a command is called.
    # Designed for usage in multiple discord guilds.

    async def cog_load(self):
        print(f"{self.__class__.__name__} loaded!")


async def setup(bot):
    # finally, adding the cog to the bot
    await bot.add_cog(MusicCog(bot=bot))
