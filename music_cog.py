import discord
import swannybottokens
from discord.ext import commands
from youtube_dl import YoutubeDL
import wavelink

class GuildInfo:
    def __init__(self, channel):
        self.is_playing = False
        self.is_paused = False
        self.music_queue = []
        self.vc = None
        self.voice_channel = channel

class music_cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guilds = {}
        bot.loop.create_task(self.connect_nodes())

    @commands.Cog.listener()
    async def on_wavelink_node_ready (self,node: wavelink.Node):
        #Event fired when a node has finished connecting
        print(f'Node <{node.identifier} is ready')

    async def connect_nodes(self):
        #to connect to wavelink nodes
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot=self.bot,
                                            host='127.0.0.1',
                                            port=2333,
                                            password=swannybottokens.WavelinkPassword)

    async def play_next(self, ctx):
        guild = self.guilds[ctx.guild.id]
        if len(guild.music_queue) > 0:
            guild.is_playing = True
            search = guild.music_queue[0][0]
            guild.music_queue.pop(0)
            await guild.voice_client.play(search)
        else:
            guild.is_playing = False

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
            player=guild.voice_client
            #await player.play(search),after=lambda e: self.play_next(ctx)
        else:
            guild.is_playing = False

    # Play Function
    @commands.command(name="play", aliases=["p", "playing"], help="Play the selected song from youtube")
    async def play(self, ctx: commands.Context, *,search: wavelink.YouTubeTrack):
        if ctx.author.voice == None:
            await ctx.send("Connect to a voice channel!")
            return
        voice_channel = ctx.author.voice.channel
        if ctx.guild.id not in self.guilds:
            self.guilds[ctx.guild.id] = GuildInfo(ctx.author.voice.channel)
        guild = self.guilds[ctx.guild.id]
        if voice_channel is None:
            await ctx.send("Connect to a voice channel!")
        elif guild.is_paused:
            guild.vc.resume()
        else:
            await ctx.send("Song added to the queue")
            guild.music_queue.append([search, voice_channel])
            if not ctx.voice_client:
                guild.voice_client = wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            else:
                vc: wavelink.Player = guild.voice_client
            if not guild.is_playing:
               await self.play_music(ctx)

    # Pause Function
    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        currentguild = self.guilds[ctx.guild.id]
        if currentguild.is_playing:
            currentguild.is_playing = False
            currentguild.is_paused = True
            ctx.voice_client.pause()
        elif self.is_paused:
            currentguild.is_playing = True
            currentguild.is_paused = False
            ctx.voice_client.resume()

    # Resume Function
    @commands.command(name="resume", aliases=["r"], help="Resumes playing the current song")
    async def resume(self, ctx, *args):
        currentguild = self.guilds[ctx.guild.id]
        if currentguild.is_paused:
            currentguild.is_playing = True
            currentguild.is_paused = False
            ctx.voice_client.resume()

    # Skip Function
    @commands.command(name="skip", aliases=["s"], help="Skips the song currently playing")
    async def skip(self, ctx, *args):
        currentguild = self.guilds[ctx.guild.id]
        if currentguild.vc is not None and currentguild.is_playing:
            currentguild.vc.stop()
            await self.play_music(ctx)

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
        if currentguild.vc is not None and currentguild.is_playing:
            currentguild.vc.stop()
        currentguild.music_queue = []
        await ctx.send("Music queue cleared")

    # Leave Function
    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kick the bot from the voice channel")
    async def leave(self, ctx):
        currentguild = self.guilds[ctx.guild.id]
        currentguild.is_playing = False
        currentguild.is_paused = False
        await ctx.voice_client.disconnect()
