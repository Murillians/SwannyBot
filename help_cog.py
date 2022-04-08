from discord.ext import commands


class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_message = """
```
General commands:
!help - Displays all the available commands.
!play, !p <keywords> - Finds the song on youtube and plays it in your current channel. Will resume playing the current song if it was paused.
    Will automatically add a song to queue if one is already playing.
!queue, !q - Displays the current music queue.
!skip, !s - Skips the current song being playing.
!clear, !c, !bin - Stops the music and clears the queue.
!leave, !disconnect, !l, !d - Disconnects Swanny Bot from the voice channel.
!pause - Pauses the current song being played or resumes if already paused.
!resume - Resumes playing the current song.      
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
