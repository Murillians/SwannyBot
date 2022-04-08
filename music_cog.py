import discord
from discord.ext import commands
from youtube_dl import YoutubeDL


class GuildInfo:
    def __init__(self, channel):
        self.is_playing = False
        self.is_paused = False
        self.music_queue = []
        self.vc = None
        self.voice_channel = channel

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}
        self.guilds={}
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception:
                return False
        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self,ctx):
        guild = self.guilds[ctx.guild]
        if len(guild.music_queue) > 0:
            guild.is_playing = True
            m_url = guild.music_queue[0][0]['source']
            guild.music_queue.pop(0)
            guild.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            guild.is_playing = False

    async def play_music(self, ctx):
        guild = self.guilds[ctx.guild]
        if len(guild.music_queue) > 0:
            guild.is_playing = True
            m_url = guild.music_queue[0][0]['source']
            if guild.vc == None or not guild.vc.is_connected():
                guild.vc = await guild.music_queue[0][1].connect()
                if guild.vc == None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                await guild.vc.move_to(guild.music_queue[0][1])
            guild.music_queue.pop(0)
            guild.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            guild.is_playing = False

    # Play Function
    @commands.command(name="play", aliases=["p", "playing"], help="Play the selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)
        voice_channel = ctx.author.voice.channel
        if self.guilds[ctx.guild] == None:
            self.guilds[ctx.guild] = GuildInfo(ctx.author.voice.channel)
        guild = self.guilds[ctx.guild]
        if voice_channel is None:
            await ctx.send("Connect to a voice channel!")
        elif guild.is_paused:
            guild.vc.resume()
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format, try a different keyword")
            else:
                await ctx.send("Song added to the queue")
                guild.music_queue.append([song, voice_channel])
                if guild.is_playing == False:
                    await self.play_music(ctx)

    # Pause Function
    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    # Resume Function
    @commands.command(name="resume", aliases=["r"], help="Resumes playing the current song")
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    # Skip Function
    @commands.command(name="skip", aliases=["s"], help="Skips the song currently playing")
    async def skip(self, ctx, *args):
        if self.vc is not None and self.vc:
            self.vc.stop()
            await self.play_music(ctx)

    # Queue Function
    @commands.command(name="queue", aliases=["q"], help="Displays all the songs currently in queue")
    async def queue(self, ctx):
        retval = "Up Next: \n"
        for i in range(0, len(self.music_queue)):
            if i > 4:
                break
            retval += self.music_queue[i][0]['title'] + '\n'
        if retval != "Up Next: \n":
            await ctx.send(retval)
        else:
            await ctx.send("No music in the queue.")

    # Clear Queue Function
    @commands.command(name="clear", aliases=["c", "bin"], help="Stops the current song and clears the queue")
    async def clear(self, ctx, *args):
        if self.vc is not None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Music queue cleared")

    # Leave Function
    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kick the bot from the voice channel")
    async def leave(self, ctx):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()
