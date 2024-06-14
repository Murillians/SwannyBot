import discord
from discord import app_commands
from discord.ext import commands
import requests
import json

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
        max_length=600,
    )

    async def on_submit(self, interaction: discord.Interaction):
        api_url = "https://www.cheapshark.com/api/1.0/deals?steamAppID="
        cheapshark_link = "https://www.cheapshark.com/redirect?dealID="
        store_link = self.feedback.value
        if "store.steampowered.com" not in store_link:
            await interaction.response.send_message(f'Sorry, I did not recognize your Steam store link!',
                                                    ephemeral=True)
        else:
            try:
                # Parse for the steam app ID from the link then break
                app_id = ""
                id_hit = False
                for i in store_link:
                    if app_id != "" and id_hit is False:
                        break
                    if i.isdigit():
                        id_hit = True
                        app_id = app_id + i
                    else:
                        id_hit = False

                fixed_api_url = api_url + app_id
                payload = {}
                headers = {}

                response = requests.request("GET", fixed_api_url, headers=headers, data=payload)
                # Pretty Print JSON Formatter
                parsed = json.loads(response.text)
                deal_id = parsed[0]["dealID"]
                print(json.dumps(parsed, indent=3))

                fixed_cheapshark_link = cheapshark_link + deal_id
                await interaction.response.send_message(fixed_cheapshark_link, ephemeral=True)

                # Return game deal with 2 buttons, close and track game

            except Exception as e:
                print(e)
                return

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
        await ctx.send('Please select an option:', view=view, ephemeral=True)
        # Wait for the View to stop listening for input...
        await view.wait()


# Define a simple View that gives us a confirmation menu
class GameDealHub(discord.ui.View):
    def __init__(self):
        super().__init__()

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="View Tracked Games", style=discord.ButtonStyle.green)
    async def view_tracked_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Lookup/Add Game', style=discord.ButtonStyle.red)
    async def add_new_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GameTrackModal())
        self.stop()

    # todo: finish after cog is done.
    @discord.ui.button(label='Help', style=discord.ButtonStyle.grey)
    async def game_deal_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            '# I support markdown!\n To share a game from the steam client, scroll down to the Share button on the right',
            ephemeral=True)
        self.stop()


async def setup(bot):
    await bot.add_cog(GameDealCog(bot=bot))
