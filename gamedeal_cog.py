import discord
from discord import app_commands
from discord.ext import commands
import requests
import json
import database

import traceback

import swannybottokens

# The guild in which this slash command will be registered.
swancord = discord.Object(swannybottokens.swancord)
active_stores = []


# Check for active stores on boot
def store_check(stores):
    # Global active stores list
    stores_url = "https://www.cheapshark.com/api/1.0/stores"

    payload = {}
    headers = {}

    response = requests.request("GET", stores_url, headers=headers, data=payload)
    if response.status_code == 200:

        stores_data = response.json()

        stores_list = stores
        for store in stores_data:
            stores_dict = {
                'storeID': store['storeID'],
                'storeName': store['storeName'],
                'isActive': store['isActive'],
            }
            if stores_dict['isActive'] == 1:
                stores_list.append(stores_dict)

        return stores_list


store_check(active_stores)


class GameDealCog(commands.Cog, name="GameDealCog"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="game_deals", description="View or add tracked game deals")
    @app_commands.guilds(swancord)
    async def ask(self, ctx: commands.Context):
        user = str(ctx.message.author)
        # We create the view and assign it to a variable so we can wait for it later.
        view = GameDealHub(user)
        await ctx.send('Please select an option:', view=view, ephemeral=True)
        # Wait for the View to stop listening for input...
        await view.wait()


# Main Menu View that returns from slash command
class GameDealHub(discord.ui.View):
    def __init__(self, user):
        super().__init__()
        self.user = user

    @discord.ui.button(label="View Tracked Games", style=discord.ButtonStyle.green)
    async def view_tracked_games(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = DropdownView(self.user)
        await interaction.response.send_message("Select from your list of tracked games:",
                                                view=view, ephemeral=True)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Lookup/Track Game', style=discord.ButtonStyle.red)
    async def lookup_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GameLookupModal(self.user))
        self.stop()

    # todo: finish after cog is done.
    @discord.ui.button(label='Help', style=discord.ButtonStyle.grey)
    async def game_deal_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            '# I support markdown!\n'
            'To share a game from the steam client, scroll down to the Share button on the right\n',
            ephemeral=True)
        self.stop()


# Dropdown List for "View Tracked Games" Button
class DropdownView(discord.ui.View):
    def __init__(self, user):
        super().__init__()
        self.user = user

        # Adds the dropdown to our view object.
        self.add_item(Dropdown(self.user))


# Defines a custom Select containing colour options
# that the user can choose. The callback function
# of this class is called when the user changes their choice
class Dropdown(discord.ui.Select):
    def __init__(self, user):
        self.user = user
        self.dbhandler = database.dbhandler()
        self.games = self.dbhandler.execute("SELECT title, steam_app_id FROM game_tracker WHERE user = ? LIMIT 25", (self.user,))
        game_list = self.games.fetchall()
        print(game_list)
        # for game in game_list:
        #     print(game["title"])
        # Set the options that will be presented inside the dropdown
        options = []
        for game in game_list:
            options = options + [
                discord.SelectOption(label=game["steam_app_id"], description=game["title"])
            ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder='Select Game', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        tracked_game = True
        app_id = self.values[0]
        print(self.values)
        game_lookup = GameLookupModal(self.user).on_submit(interaction, app_id, tracked_game)
        await game_lookup


# Modal popup on "Lookup/Track Game" Button
class GameLookupModal(discord.ui.Modal, title="Game Lookup"):
    def __init__(self, user, tracked_game=False):
        self.user = user
        self.tracked_game = tracked_game
        super().__init__()

    # User enters link with max of 600 characters
    feedback = discord.ui.TextInput(
        label='store.steampowered.com link to game',
        style=discord.TextStyle.long,
        placeholder='Insert Link',
        required=False,
        max_length=600,
    )

    # Logic after store link submission
    async def on_submit(self, interaction: discord.Interaction, app_id="", tracked_game=False):
        api_url = "https://www.cheapshark.com/api/1.0/deals?steamAppID="
        cheapshark_link = "https://www.cheapshark.com/redirect?dealID="
        store_link = self.feedback.value
        if app_id == "" and "store.steampowered.com" not in store_link:
            await interaction.response.send_message(f'Sorry, I did not recognize your Steam store link!',
                                                    ephemeral=True)
            return
        elif app_id == "":
            # Parse for the steam app ID from the link then break
            id_hit = False
            for i in store_link:
                if app_id != "" and id_hit is False:
                    break
                if i.isdigit():
                    id_hit = True
                    app_id = app_id + i
                else:
                    id_hit = False

        # Build request to cheapshark API
        fixed_api_url = api_url + app_id
        payload = {}
        headers = {}

        response = requests.request("GET", fixed_api_url, headers=headers, data=payload)
        parsed = json.loads(response.text)

        # Build the response message with all the stores available where the game is on sale
        on_sale_stores = ""
        not_sale_stores = ""
        title = ""
        sale_price = ""
        is_on_sale = ""
        for i in parsed:
            deal_id = i["dealID"]
            store_id = i["storeID"]
            title = i["title"]
            sale_price = i["salePrice"]
            normal_price = i["normalPrice"]
            savings = round(float(i["savings"]))
            is_on_sale = int(i["isOnSale"])

            store_name = ""
            for j in active_stores:
                if store_id == j["storeID"]:
                    store_name = j["storeName"]
                    break

            if is_on_sale == 1:
                on_sale_stores = (
                        on_sale_stores +
                        f"# [{store_name}](<{cheapshark_link}{deal_id}>) | **${sale_price}**\n"
                        f"### ~~${normal_price}~~ | `-{savings}% OFF`\n"
                )
            elif is_on_sale == 0:
                not_sale_stores = (
                        not_sale_stores +
                        f"[{store_name}](<{cheapshark_link}{deal_id}>) | **${sale_price}** `MSRP`\n"
                )

        response_message = (f"# __{title}__\n\n" + on_sale_stores + not_sale_stores +
                            "Waiting for a better deal? Track this game below now:\n")

        # Pretty Print JSON Formatter
        # print(json.dumps(parsed, indent=3))
        if not self.tracked_game:
            view = ViewOnLookup(app_id, is_on_sale, sale_price, self.user, title)
            await interaction.response.send_message(response_message, view=view, ephemeral=True)
            # Wait for the View to stop listening for input...
            await view.wait()
        else:
            await interaction.response.send_message(response_message, ephemeral=True)

        # return app_id, user, is_on_sale, sale_price

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)


# Track Game Button after Game Lookup returns successful
class ViewOnLookup(discord.ui.View):
    def __init__(self, app_id, is_on_sale, sale_price, user, title):
        super().__init__()
        self.dbhandler = database.dbhandler()
        self.app_id = app_id
        self.is_on_sale = is_on_sale
        self.sale_price = sale_price
        self.user = user
        self.title = title

    @discord.ui.button(label="Track Game", style=discord.ButtonStyle.red)
    async def track_game_on_lookup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('This game is now being tracked. '
                                                'You will be notified when it goes on sale again!', ephemeral=True)
        # todo: Conditional to bar from tracking duplicates as well as 25 entry limit check. duplicates WILL BREAK the dropdown selector
        self.dbhandler.execute("INSERT INTO game_tracker VALUES(?,?,?,?,?)",
                               (self.app_id, self.is_on_sale, self.sale_price, self.user, self.title))
        self.dbhandler.commit()
        self.stop()


async def setup(bot):
    await bot.add_cog(GameDealCog(bot=bot))
