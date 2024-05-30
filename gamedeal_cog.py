import discord
from discord import app_commands
from discord.ext import commands

import traceback

import swannybottokens

# The guild in which this slash command will be registered.
swancord = discord.Object(swannybottokens.swancord)


class GameDealCog(commands.Cog, name="GameDealCog"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="Track Game Deal",
            callback=self.track_game
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def track_game(self, interaction: discord.Interaction, message: discord.Message):
        # Send the modal with an instance of our `GameDealCog` class
        # Since modals require an interaction, they cannot be done as a response to a text command.
        # They can only be done as a response to either an application command or a button press.
        await interaction.response.send_message("Hello")

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    # User enters title
    name = discord.ui.TextInput(
        label='Title',
        placeholder='Insert Game Title',
    )

    # User enters link with max of 300 characters
    feedback = discord.ui.TextInput(
        label='Store link to game',
        style=discord.TextStyle.long,
        placeholder='Insert Link',
        required=False,
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'{self.name.value} is now set up for deal alerts!', ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)


async def setup(bot):
    await bot.add_cog(GameDealCog(bot=bot))
