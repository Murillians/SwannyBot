import discord
import asyncio
import threading
import swannybottokens
import wavelink
import typing
from discord.ext import commands,tasks
from wavelink.ext import spotify
import logging
from enum import Enum


class Status(Enum):
    playing = 1
    paused = 2
    stopped = 3
    disconnected=4


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
    #connect function, mostly helper
    @commands.command()
    async def connect(self,ctx : commands.Context, *, channel: discord.VoiceChannel = None):
        try:
            channel=channel or ctx.author.voice.channel
        except AttributeError:
            return await ctx.send("Connect to a voice channel!")
            raise Exception()
        vc: wavelink.Player=await channel.connect(cls=wavelink.Player)
        return vc

    # Play Function
    @commands.command(name="play", aliases=["p", "playing"], help="Play the selected song from youtube")
    async def play(self, ctx: commands.Context, *,
                   track: typing.Union[wavelink.YouTubeTrack, wavelink.SoundCloudTrack]):
        if ctx.guild.id not in self.guilds:
            self.guilds[ctx.guild.id] = GuildInfo(ctx.author.voice.channel)
        guild = self.guilds[ctx.guild.id]
        if guild.voice_client is None:
            try:
                guild.voice_client = await self.connect(ctx)
            except Exception:
                #could not connect to the voice channel for some reason, stop trying to connect
                return
        if guild.voice_client.is_playing() or guild.voice_client.queue.count > 0:
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
                await guild.voice_client.play(guild.voice_client.queue.get())
                guild.status = Status.playing
        #else:
          #  guild.voice_client = wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
         #   guild.voice_client.queue.put(track)
         #   songEmbed = discord.Embed(
         #       title=track.title + " added to queue",
          #      url=track.uri
          #  ).set_image(url=track.thumb).set_thumbnail(url=track.thumbnail)
          #  await ctx.send(embed=songEmbed)
         #   await guild.voice_client.play(guild.voice_client.queue.get())
          #  guild.status = Status.playing

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
            await currentguild.voice_client.resume()

    # Skip Function
    @commands.command(name="skip", aliases=["s"], help="Skips the song currently playing")
    async def skip(self, ctx, *args):
        currentguild = self.guilds[ctx.guild.id]
        if currentguild.voice_client is not None and currentguild.status == Status.playing:
            await currentguild.voice_client.stop()

    # Queue Function
    # todo: FIX
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
        if currentguild.voice_client is not None and currentguild.status == Status.playing:
            await currentguild.voice_client.stop()
            currentguild.voice_client.queue.clear()
        await ctx.send("Music queue cleared")

    # Leave Function
    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kick the bot from the voice channel")
    async def leave(self, ctx):
        currentguild = self.guilds[ctx.guild.id]
        currentguild.status=Status.disconnected
        currentguild.voice_client.queue.clear()
        await ctx.voice_client.disconnect()
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        if player.queue.count > 0:
            await player.play(player.queue.get())
        else:
            guild = self.guilds[player.guild.id]
            guild.status = Status.stopped
            await asyncio.sleep(600)
            if player.is_playing() is not True:
                await self.timeout(guild)
    @commands.Cog.listener()
    async def on_wavelink_websocket_closed(player: wavelink.Player, reason, code):
        logging.info("wavelink websocket closed, Reason: "+reason+" Code: "+code)
    @commands.Cog.listener()
    async def on_wavelink_track_exception(player: wavelink.Player, track: wavelink.Track, error):
        logging.info("wavelink track error, Error: "+error+" track: "+track)

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(player: wavelink.Player, track: wavelink.Track, threshold):
        logging.info("wavelink track stuck, Threshold: "+threshold+" track: "+track)



    async def timeout(self,guild):
        currentguild = guild
        currentguild.is_playing = False
        currentguild.is_paused = False
        await currentguild.voice_client.disconnect()
