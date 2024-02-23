import asyncio
import discord
from discord.ext import commands
import wavelink


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
    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str):
        wavelink_player = self.get_current_player(ctx)

        # Try to get the current player. If not found, connect.
        if wavelink_player is None:
            wavelink_player: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        # Autoplay Function that runs the queue.
        # Setting the mode to partial will run the queue without recommendations.
        if not wavelink_player.playing:
            wavelink_player.autoplay = wavelink.AutoPlayMode.partial

        # Begin search for a playable to add to queue.
        tracks: wavelink.Search = await wavelink.Playable.search(query)

        # Send an error if none of the parses could find a song.
        if tracks is None:
            await ctx.reply("Sorry, I could not find your song!")
            return

        # Determine the playable
        user = ctx.message.author
        if isinstance(tracks, wavelink.Playlist):
            # tracks is a playlist...
            added: int = await wavelink_player.queue.put_wait(tracks)
            await ctx.send(embed=discord.Embed(
                title=tracks.name,
                url=query,
                description=tracks.author,
                color=discord.Color.red())
                .set_author(
                name=f"{user.display_name} added a playlist to the queue",
                icon_url=user.avatar)
                .set_footer(
                text=f"Duration: {added} songs"
            ))
        else:
            track: wavelink.Playable = tracks[0]
            await wavelink_player.queue.put_wait(track)
            await ctx.send(embed=discord.Embed(
                title=track.title,
                url=track.uri,
                description=track.author,
                color=discord.Color.red())
                .set_author(
                name=f"{user.display_name} added a song to the queue",
                icon_url=user.avatar)
                .set_thumbnail(
                url=track.artwork)
                .set_footer(
                text="Song Length: " + self.timestamp(track.length)))

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

        await self.empty_channel(ctx)

    # Autoplay Toggle Function
    @commands.command(name="autoplay", aliases=["ap"])
    async def autoplay(self, ctx: commands.Context):
        wavelink_player: wavelink.Player = self.get_current_player(ctx)
        if wavelink_player is None:
            wavelink_player: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        if wavelink_player.autoplay == wavelink.AutoPlayMode.partial:
            await ctx.reply("Okay, I will start looking for recommended tracks based on your queries!")
            wavelink_player.autoplay = wavelink.AutoPlayMode.enabled
        else:
            await ctx.reply("No problem, I will stop looking for recommended tracks!")
            wavelink_player.autoplay = wavelink.AutoPlayMode.partial

    # Command to add song to an established queue and play it next.
    @commands.command(name="playnext", aliases=["pn"])
    async def play_next(self, ctx: commands.Context, *, query: str):
        temp_ctx = ctx
        temp_query = query
        await self.play(temp_ctx, query=temp_query)
        wavelink_player = self.get_current_player(ctx)
        current_queue = wavelink_player.queue
        last_added = current_queue[-1]
        current_queue.put_at(0, last_added)
        current_queue.delete(-1)
        await ctx.send("This song is playing next! 👆")

    @commands.command(name="remove", aliases=["rm"])
    async def remove(self, ctx: commands.Context, *, position: int):
        wavelink_player = self.get_current_player(ctx)
        current_queue = wavelink_player.queue
        # The true position of the next song is 0, but end user only sees 1, so subtract by 1.
        true_position = position - 1
        if position is None or not int or position <= 0:
            await ctx.send("You must specify a numeric position in the queue to remove a song. "
                           "Type **!queue** to see the upcoming positions.")
        else:
            current_queue.delete(true_position)
            await ctx.send(f"The song in position `{position}.` was removed from the queue!")

    # Pause Function
    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        wavelink_player = self.get_current_player(ctx)
        if not await wavelink_player.pause(True):
            await wavelink_player.pause(True)
        else:
            await wavelink_player.pause(False)

    # Resume Function
    @commands.command(name="resume", aliases=["r"])
    async def resume(self, ctx, *args):
        wavelink_player = self.get_current_player(ctx)
        if wavelink_player.pause(True):
            await wavelink_player.pause(False)

    # Skip Function
    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx, *args):
        wavelink_player = self.get_current_player(ctx)
        if wavelink_player is not None and wavelink_player.playing:
            await wavelink_player.skip()
            await ctx.message.add_reaction("<:ThumbsUp:936340890086158356>")

    # Time Embed Helper
    def timestamp(self, milliseconds):
        seconds = milliseconds // 1000
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour == 0:
            return "%02d:%02d" % (minutes, seconds)
        else:
            return "%02d:%02d:%02d" % (hour, minutes, seconds)

    # Queue Embed Function
    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):
        wavelink_player = self.get_current_player(ctx)
        current_queue = wavelink_player.queue
        autoplay_queue = wavelink_player.auto_queue
        current_tracks = ""
        auto_tracks = ""
        queue_length = 0
        autoplay_on = ""
        queue_on = ""
        try:
            # Current Queue Embed Counter
            for i in range(0, len(wavelink_player.queue)):
                if i > 4:
                    break
                current_tracks += ('`' + str(i+1) + '.` ' + current_queue[i].title + ' - **'
                                   + current_queue[i].author + '**'
                                   + ' `' + self.timestamp(current_queue[i].length)
                                   + '`\n')
            # Current Queue Duration Counter
            for i in range(0, len(wavelink_player.queue)):
                queue_length += current_queue[i].length
            total_duration = self.timestamp(queue_length)
            # Auto Queue Embed Counter
            for i in range(0, len(wavelink_player.auto_queue)):
                if i > 4:
                    break
                auto_tracks += ('`' + str(i+1) + '.` ' + autoplay_queue[i].title + ' - **'
                                + autoplay_queue[i].author + '**'
                                + ' `' + self.timestamp(autoplay_queue[i].length)
                                + '`\n')
            # If autoplay is enabled, display the auto queue embed
            if wavelink_player.autoplay == wavelink.AutoPlayMode.enabled:
                autoplay_on = "Auto Queue:"
            # If the queue contains tracks, display the current queue embed
            if len(wavelink_player.queue) != 0:
                queue_on = "Current Queue:"
            # Queue Rich Embed
            if wavelink_player.playing:
                await ctx.send(embed=discord.Embed(
                    title=wavelink_player.current.title,
                    description=wavelink_player.current.author + ' `'
                                + self.timestamp(wavelink_player.current.length) + '`',
                    color=discord.Color.from_rgb(115, 112, 175))
                    .set_author(
                    name="Now Playing",
                    icon_url="https://i.imgur.com/s9gbmVq.png")
                    .set_thumbnail(
                    url=wavelink_player.current.artwork)
                    .add_field(
                    name=queue_on,
                    value=current_tracks,
                    inline=False)
                    .add_field(
                    name=autoplay_on,
                    value=auto_tracks,
                    inline=False)
                    .set_footer(
                    text="Current Queue Duration: %s songs, %s" % (len(current_queue), total_duration)))
            else:
                await ctx.send(embed=discord.Embed(
                    title="No tracks in the queue!",
                    description="Add more tracks with **!play** or keep the party going with **!autoplay**",
                    color=discord.Color.from_rgb(115, 112, 175))
                    .set_author(
                    name="Uh Oh...",
                    icon_url="https://i.imgur.com/s9gbmVq.png")
                    .set_footer(
                    text="The music session will be ending soon!"))
        except Exception as e:
            print(e)
            await ctx.send("No music in the queue.")
            pass

    # Shuffle Queue Function
    @commands.command(name="shuffle", aliases=["shuf"])
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
    @commands.command(name="clear", aliases=["c", "bin"])
    async def clear(self, ctx, *args):
        wavelink_player = self.get_current_player(ctx)
        if wavelink_player is not None and wavelink_player.playing:
            wavelink_player.queue.clear()
            await wavelink_player.stop()
            await ctx.send("The music queue was cleared!")

    # Leave Function
    @commands.command(name="leave", aliases=["disconnect", "l", "d"])
    async def leave(self, ctx):
        wavelink_player = self.get_current_player(ctx)
        wavelink_player.queue.clear()
        await wavelink_player.disconnect()

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        # Swanny Bot says "Bye Bye!" then disconnects
        tracks: wavelink.Search = await wavelink.Playable.search("https://www.youtube.com/watch?v=Sx3nXA23jjo")
        track: wavelink.Playable = tracks[0]
        await player.play(track)
        await asyncio.sleep(3)
        await player.disconnect()

    # Check every 10 minutes while playing if Swanny Bot is the only member in connected voice channel
    # Note: If nothing is playing, inactive_player will disconnect instead
    async def empty_channel(self, ctx: commands.Context) -> None:
        current_voice_channel = ctx.author.voice.channel
        wavelink_player: wavelink.Player = self.get_current_player(ctx)
        while wavelink_player.playing:
            await asyncio.sleep(600)
            try:
                if current_voice_channel.members[0].bot and len(current_voice_channel.members) == 1:
                    await wavelink_player.disconnect()
                    break
            except Exception as e:
                print(e)
                pass

    # Check every 5 minutes while playing if Swanny Bot is the only member in connected voice channel
    # If nothing is playing, inactive_player will disconnect instead
    @commands.Cog.listener()
    async def empty_channel(self, player: wavelink.Player, ctx: commands.Context) -> None:
        current_voice_channel = ctx.author.voice.channel
        await asyncio.sleep(5)
        if player.playing:
            print(current_voice_channel.id)
            print(current_voice_channel.name)
            print(current_voice_channel.members)
            print(self.bot.user.id)
            if current_voice_channel.members == self.bot.get_user(id(self)):
                await player.disconnect()


    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            return

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
