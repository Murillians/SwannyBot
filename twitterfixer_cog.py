import discord
from discord.ext import commands
from urllib.parse import urlparse
import swannybottokens


class twitterfixer_cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def twitterfixer(self,message:discord.Message):
        if "twitter.com" in message.content or "x.com" in message.content:
            fixedLink=""
            if message.content.split(' ').__len__() <2:
                link=urlparse(message.content)
                fixedLink=link.scheme+"://"+"vxtwitter.com"+link.path
                print(fixedLink)
            else:
                return
            msgChannel=message.channel
            #msgAuthor=await self.bot.get_user(message.author.id)
            msgAuthor=message.author
            try:
                success=await msgChannel.send(content=f"{msgAuthor.mention}: {fixedLink}",silent=True)
            except Exception as e:
                print(e)
                return
            await message.delete()



    @commands.Cog.listener('on_message')
    async def on_message(self,message: discord.Message):
        if message.guild.id == swannybottokens.swancord:
            await self.twitterfixer(message)