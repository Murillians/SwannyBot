import discord
from discord.ext import commands
from urllib.parse import urlparse
import swannybottokens


class twitterfixer_cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def twitterfixer(self,message:discord.Message):
        #in order
        #1: make sure the author is NOT swanny bot to prevent recursion
        #2: dont do it if its a command
        #3: make sure theres a twitter/x link SOMEWHERE in the message
        if  message.author.id != swannybottokens.swannybotid and message.content[0] != "!" and "twitter.com" in message.content or "x.com" in message.content:
            fixedMsg=""
            splitMsg = message.content.split(' ')
            #this is just a message with the twitter link
            if splitMsg.__len__() <2:
                link=urlparse(message.content)
                fixedMsg=link.scheme+"://"+"vxtwitter.com"+link.path
                print(fixedMsg)
            #this is a message with a twitter link in it somewhere
            elif splitMsg.__len__() >=2:
                for string in splitMsg:
                    linkTest = urlparse(string)
                    #found a twitter link, fix it
                    if linkTest.hostname is not None:
                        temp = "".join([linkTest.scheme, "://"+"vxtwitter.com",linkTest.path," "])
                        print(temp)
                        fixedMsg+=temp
                    #not a twitter link, keep going
                    else:
                        fixedMsg+=string
                        fixedMsg+=" "

            msgChannel=message.channel
            msgAuthor=message.author
            #send back the message to discord with a "silent" flag so it doesnt re ping for the same message that was just sent
            try:
                success=await msgChannel.send(content=f"{msgAuthor.mention}: {fixedMsg}",silent=True)
            except Exception as e:
                print(e)
                return
            #delete the original message so there arent two of the same msg in discord, if we want to keep the orig
            #comment this line out
            await message.delete()



    @commands.Cog.listener('on_message')
    async def on_message(self,message: discord.Message):
        if message.guild.id == swannybottokens.swancord:
            await self.twitterfixer(message)