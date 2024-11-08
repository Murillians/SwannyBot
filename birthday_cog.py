import discord
from discord import app_commands
from discord.ext import tasks, commands
import requests
import json
import database
import datetime
from dateutil import tz

import traceback

import swannybottokens

# The guild(s) in which this slash command will be registered.
swancord = discord.Object(swannybottokens.swancord)
boyscord = discord.Object(swannybottokens.jesuscord)


class BirthdayCog(commands.Cog, name="BirthdayCog"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.dbhandler = database.dbhandler()

    @commands.hybrid_command(name="birthdays", description="View or add a birthday.")
    @app_commands.guilds(swancord, boyscord)
    async def ask(self, ctx: commands.Context):
        user = str(ctx.message.author)
        user_id = ctx.message.author.id
        guild_id = ctx.message.guild.id
        view = BirthdayMenu(user, user_id, guild_id)
        await ctx.send('Please select an option:', view=view, ephemeral=True)
        await view.wait()


# Main Menu View that returns from slash command
class BirthdayMenu(discord.ui.View):
    def __init__(self, user, user_id, guild_id):
        super().__init__()
        self.user = user
        self.user_id = user_id
        self.guild_id = guild_id
        self.dbhandler = database.dbhandler()

    @discord.ui.button(label='Help', style=discord.ButtonStyle.grey)
    async def birthday_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("todo", ephemeral=True)
        self.stop()


async def setup(bot):
    await bot.add_cog(BirthdayCog(bot=bot))