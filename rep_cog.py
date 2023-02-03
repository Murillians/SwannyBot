from discord.ext import commands
import datetime
import sqlite3

import swannybottokens


class rep_cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    #todo: Add in database connection via singleton call to a DB helper class?

    #background function to count +rep and -rep emoji across all messages in a server every 12 hours
    #counts the number of +rep and -rep emoji on a message and adds them to the user's total
    #would need to store last time it checked+date/time checked (from X to Y) to be able to recover after failure
    #refer to https://discordpy.readthedocs.io/en/stable/api.html?highlight=message%20react#discord.TextChannel.history
    @commands.command("reactionCounter")
    async def reactionCounter(self,ctx):
        channel = self.bot.get_channel(swannybottokens.nsfw_channel) #hardcoded for testing
        plusRep=0
        minusRep=0
        thistbh=0
        afterTime = (datetime.datetime.now())-datetime.timedelta(days=7)
        messages=[message async for message in channel.history(after=afterTime)]
        for message in messages:
            if len(message.reactions) < 1:
                continue
            for reaction in message.reactions:
                if reaction.is_custom_emoji():
                    if reaction.emoji.name=="positiverepu":
                        plusRep += reaction.count
                    elif reaction.emoji.name=="negativerepu":
                        minusRep += reaction.count
                    elif reaction.emoji.name=="thistbh":
                        thistbh +=reaction.count
        message = ("since "+" we have had\n")
        message = message + (str(plusRep)+" reacts of :positiverepu:\n")
        message = message +(str(minusRep) + " reacts of :minusrepu:\n")
        message = message +(str(thistbh) + " reacts of :thistbh:\n")
        message = message +(" in "+channel.name.title()+"\n")
        print(message)
        await ctx.channel.send(message)

