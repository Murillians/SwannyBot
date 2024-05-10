import discord
from discord import app_commands
from discord.ext import commands
from urllib.parse import urlparse
import swannybottokens


class twitterfixer_cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="Twitter Link Fixer",
            callback=self.twitterfixer
        )
        self.bot.tree.add_command(self.ctx_menu)
    async def twitterfixer(self,interaction: discord.Interaction, message: discord.Message):
        try:
            if message.content[0] != "!" and ("twitter.com" in message.content or "x.com" in message.content):
                fixedLinks=""
                tempmsg=message.content.replace('\n', " ")
                splitMsg = tempmsg.split(" ")
                #this is just a message with the twitter link
                if splitMsg.__len__() <2:
                    link = urlparse(message.content)
                    fixedLinks = link.scheme+"://"+"vxtwitter.com"+link.path
                    print(fixedLinks)
                #this is a message with a twitter link in it somewhere
                elif splitMsg.__len__() >=2:
                    for string in splitMsg:
                        linkTest = urlparse(string)
                        #found a twitter link, fix it
                        if linkTest.hostname is not None:
                            temp = "".join([linkTest.scheme, "://"+"vxtwitter.com",linkTest.path,'\n'])
                            print(temp)
                            fixedLinks+=temp

                #send back the message to discord with a "silent" flag so it doesnt re ping for the same message that was just sent
                try:
                    success=await message.reply(content=f"{fixedLinks}",silent=True)
                    if isinstance(success,discord.Message):
                        await interaction.response.send_message(
                            content="Link successfully fixed!", ephemeral=True
                        )
                except Exception as e:
                    print(e)
                    return
        except Exception as e:
             print(e)



    #@commands.Cog.listener('on_message')
    #async def on_message(self,message: discord.Message):
    #    if message.guild.id == swannybottokens.swancord or message.guild.id == swannybottokens.jesuscord:
    #        await self.twitterfixer(message)
async def setup(bot):
    await bot.add_cog(twitterfixer_cog(bot=bot))