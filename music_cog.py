import discord

import swannybottokens
from discord.ext import commands
import wavelink
from wavelink.ext import spotify
import typing
from enum import Enum


class Status(Enum):
    playing = 1
    paused = 2
    stopped = 3


class GuildInfo:
    def __init__(self, channel):
        self.voice_client = None
        self.voice_channel = channel
        self.status = Status


class music_cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guilds = {}
        bot.loop.create_task(self.connect_nodes())

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        # Event fired when a node has finished connecting
        print(f'Node <{node.identifier} is ready')

    async def connect_nodes(self):
        # to connect to wavelink nodes
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot=self.bot,
                                            host='127.0.0.1',
                                            port=2333,
                                            password=swannybottokens.WavelinkPassword,
                                            spotify_client=spotify.SpotifyClient(client_id=swannybottokens.SpotifyID,
                                                                                 client_secret=swannybottokens.SpotifySecret))

    async def play_next(self, ctx):
        guild = self.guilds[ctx.guild.id]
        if guild.voice_client and guild.voice_client.queue.count > 0:
            guild.status = Status.playing
            await guild.voice_client.play(guild.voice_client.queue.pop())
        else:
            guild.status = Status.paused

    async def play_music(self, ctx):
        guild = self.guilds[ctx.guild.id]
        if len(guild.music_queue) > 0:
            guild.is_playing = True
            search = guild.music_queue[0][0]
            if not ctx.voice_client:
                guild.vc = await guild.music_queue[0][1].connect()
                if guild.vc == None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            guild.music_queue.pop(0)
            player = guild.voice_client
        else:
            guild.is_playing = False

    # Play Function
    #TODO:visual feedback of song after adding
    @commands.command(name="play", aliases=["p", "playing"], help="Play the selected song from youtube")
    async def play(self, ctx: commands.Context, *,
                   track: typing.Union[wavelink.YouTubeTrack, wavelink.SoundCloudTrack]):
        if ctx.author.voice == None:
            await ctx.send("Connect to a voice channel!")
            return
        voice_channel = ctx.author.voice.channel
        if ctx.guild.id not in self.guilds:
            self.guilds[ctx.guild.id] = GuildInfo(ctx.author.voice.channel)
        guild = self.guilds[ctx.guild.id]
        if voice_channel is None:
            await ctx.send("Connect to a voice channel!")
        if ctx.voice_client:
            if guild.voice_client.queue.count > 0 or guild.voice_client.is_playing():
                guild.voice_client.queue.put(track)
                songEmbed = discord.Embed(
                    title=track.title + " added to queue",
                    url=track.uri
                ).set_image(url=track.thumb).set_thumbnail(url=track.thumbnail)
                await ctx.send(embed=songEmbed)
            if guild.voice_client.queue.count == 0:
                guild.voice_client.queue.put(track)
                songEmbed = discord.Embed(
                    title=track.title + " added to queue",
                    url=track.uri
                ).set_image(url=track.thumb).set_thumbnail(url=track.thumbnail)
                await ctx.send(embed=songEmbed)
                await guild.voice_client.play(guild.voice_client.queue.pop())
                guild.status = Status.playing
        else:
            guild.voice_client = wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            guild.voice_client.queue.put(track)
            songEmbed = discord.Embed(
                title=track.title + " added to queue",
                url=track.uri
            ).set_image(url=track.thumb).set_thumbnail(url=track.thumbnail)
            await ctx.send(embed=songEmbed)
            await guild.voice_client.play(guild.voice_client.queue.pop())
            guild.status = Status.playing

    # Pause Function
    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        currentguild = self.guilds[ctx.guild.id]
        if not currentguild.voice_client.is_paused():
            currentguild.status = Status.paused
            await currentguild.voice_client.pause()
        else:
            currentguild.status = Status.playing
            await currentguild.voice_client.resume()

    # Resume Function
    @commands.command(name="resume", aliases=["r"], help="Resumes playing the current song")
    async def resume(self, ctx, *args):
        currentguild = self.guilds[ctx.guild.id]
        if currentguild.voice_client.is_paused():
            currentguild.status = Status.playing
            currentguild.voice_client.resume()

    # Skip Function
    @commands.command(name="skip", aliases=["s"], help="Skips the song currently playing")
    async def skip(self, ctx, *args):
        currentguild = self.guilds[ctx.guild.id]
        if currentguild.voice_client is not None and currentguild.status==Status.playing:
            await currentguild.voice_client.stop()
            await self.play_next(ctx)

    # Queue Function
    @commands.command(name="queue", aliases=["q"], help="Displays all the songs currently in queue")
    async def queue(self, ctx):
        currentguild = self.guilds[ctx.guild.id]
        retval = "Up Next: \n"
        for i in range(0, len(currentguild.music_queue)):
            if i > 4:
                break
            retval += currentguild.music_queue[i][0]['title'] + '\n'
        if retval != "Up Next: \n":
            await ctx.send(retval)
        else:
            await ctx.send("No music in the queue.")

    # Clear Queue Function
    @commands.command(name="clear", aliases=["c", "bin"], help="Stops the current song and clears the queue")
    async def clear(self, ctx, *args):
        currentguild = self.guilds[ctx.guild.id]
        if currentguild.voice_client is not None and currentguild.is_playing:
            currentguild.voice_channel.stop()
            currentguild.voice_channel.queue.clear()
        await ctx.send("Music queue cleared")

    # Leave Function
    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kick the bot from the voice channel")
    async def leave(self, ctx):
        currentguild = self.guilds[ctx.guild.id]
        currentguild.is_playing = False
        currentguild.is_paused = False
        await ctx.voice_client.disconnect()

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        if player.queue.count > 0:
            await player.play(player.queue.pop())
        else:
            guild = self.guilds[player.guild.id]
            guild.status = Status.playing
