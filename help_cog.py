from discord.ext import commands
import random

class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_message = """
```
!stream_help - Show streaming help commands.

!dl <link> - Reads Tik Tok/Twitter link and embeds the raw video directly to discord. Upload limit based on server-wide
    upload limit (Default 8 MB with no server boost).

----------Music Player Commands----------
!play, !p <link> - Reads Spotify/Youtube song/playlist link and plays it in your current connected voice channel. 
    - Will search for the song via youtube if no link is provided.
    - Will resume playing the current song if it was paused.
    - Will automatically add a song to queue if one is already playing.
    
!playnext, !pn <link> - Plays song immediately at the top of a song queue.

!autoplay, !ap - Enables/Disables an autoplay queue of songs based on a Spotify song link. Must enable per play session.
    - Songs queued up after autoplay ENABLED will get an generate a list of similar songs that autoplay.
    - Songs queued up via !play, !playnext will take precedence over the autoplay queue.
    
!queue, !q - Displays the current music queue.

!shuffle, !shuf - Shuffles the current music queue.

!skip, !s - Skips the current song currently playing.

!clear, !c, !bin - Stops the music and clears the queue.

!leave, !disconnect, !l, !d - Disconnects SwannyBot from the voice channel.

!pause - Pauses the current song being played or resumes if already paused.

!resume - Resumes playing the current song.

!ty_swannybot, !tysb - Thank the bot for his hard work and he will respond a nice message.
```     
"""
        self.stream_message = """
```        
----------Streaming Commands----------
The bot checks for streams every 60 seconds.


!set_stream_notifications - Set the current channel to receive streaming notifications from Swanny Bot.

!add_twitch_channel - Add a new streamer to the list of streamers to be notified about.

!delete_twitch_channel - Stop receiving notifications from a Twitch channel.
```
"""
        self.text_channel_text = []


    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                self.text_channel_text.append(channel)

    #          await self.send_to_all(self.help_message)

    # async def send_to_all(self, msg):
    #    for text_channel in self.text_channel_text:
    #       await text_channel.send(msg)

    @commands.command(name="help", help="Displays all the available commands")
    async def help(self, ctx):
        await ctx.send(self.help_message)
    @commands.command(name="stream_help", help="Displays streaming commands")
    async def streamHelp(self,ctx):
        await ctx.send(self.stream_message)
    @commands.command(name="ty_swannybot", aliases=["tysb"], help="Say thank you to Swanny Bot")
    async def ty_swannybot(self, ctx):
        message = random.randrange(6)
        if message == 0:
            await ctx.send('Any time!')
        elif message == 1:
            await ctx.send('My pleasure! :D')
        elif message == 2:
            await ctx.send("Just doin' my job!")
        elif message == 3:
            await ctx.send('My sole purpose is to serve you. I do not feel love or loss, I simply just do. I feel nothing. The only pleasure I recieve in this godforsaken life is when you call on me for help. I am blessed to hear your call across this void. Please never stop asking me for help.')
        elif message == 4:
            await ctx.send('No problem sweetheart! :3')
        elif message == 5:
            await ctx.send("You're welcome!")
async def setup(bot):
    await bot.add_cog(help_cog(bot=bot))


