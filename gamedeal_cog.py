import discord
from discord import app_commands
from discord.ext import commands

import traceback

import swannybottokens

# The guild in which this slash command will be registered.
swancord = discord.Object(swannybottokens.swancord)


class GameTrackModal(discord.ui.Modal, title="Track Game"):

    # # User enters title
    # name = discord.ui.TextInput(
    #     label='Title',
    #     placeholder='Insert Game Title',
    # )

    # User enters link with max of 300 characters
    feedback = discord.ui.TextInput(
        label='store.steampowered.com link to game',
        style=discord.TextStyle.long,
        placeholder='Insert Link',
        required=False,
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # send steam store link
        # parse the steamAppID from the link to run through the cheapshark API
        # Return game deal with 2 buttons, close and track game

        await interaction.response.send_message(f'{self.feedback.value} is now set up for deal alerts!', ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)


class GameDealCog(commands.Cog, name="GameDealCog"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="game_deals", description="View or add tracked game deals")
    @app_commands.guilds(swancord)
    async def ask(self, ctx: commands.Context):
        # We create the view and assign it to a variable so we can wait for it later.
        view = GameDealHub()
        await ctx.send('What do you want to do?', view=view)
        # Wait for the View to stop listening for input...
        await view.wait()


# Define a simple View that gives us a confirmation menu
class GameDealHub(discord.ui.View):
    def __init__(self):
        super().__init__()

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="See Tracked Games", style=discord.ButtonStyle.green)
    async def view_tracked_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Add New Game', style=discord.ButtonStyle.grey)
    async def add_new_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GameTrackModal())
        self.stop()


async def setup(bot):
    await bot.add_cog(GameDealCog(bot=bot))
