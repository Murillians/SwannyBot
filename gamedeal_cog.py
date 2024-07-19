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


def game_lookup(app_id):
    api_url = "https://www.cheapshark.com/api/1.0/deals?steamAppID="

    # Build request to cheapshark API
    fixed_api_url = api_url + app_id
    payload = {}
    headers = {}

    response = requests.request("GET", fixed_api_url, headers=headers, data=payload)
    parsed = json.loads(response.text)
    # Pretty Print JSON Formatter
    # print(json.dumps(parsed, indent=3))

    deal_id = []
    title = []
    sale_price = []
    normal_price = []
    savings = []
    is_on_sale = []
    store_name = []

    for i in parsed:
        deal_id = deal_id + [i["dealID"]]
        store_id = i["storeID"]
        title = title + [i["title"]]
        sale_price = sale_price + [i["salePrice"]]
        normal_price = normal_price + [i["normalPrice"]]
        savings = savings + [round(float(i["savings"]))]
        is_on_sale = is_on_sale + [int(i["isOnSale"])]
        for j in active_stores:
            if store_id == j["storeID"]:
                store_name = store_name + [j["storeName"]]
                break

    # Returns list variables, so we will need to iterate through all of them in other functions
    return deal_id, title, sale_price, normal_price, savings, is_on_sale, store_name


class GameDealCog(commands.Cog, name="GameDealCog"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.daily_checked = False
        self.dbhandler = database.dbhandler()

    deals_channel = 1154762810987921438  # 912393491521351800 <- this is the actual deals channel ID, currently bawt-spam

    @commands.command(name="checktest")
    async def checktest(self, ctx):
        await self.daily_sale_check()

    # Check database entries daily for sales
    @tasks.loop(seconds=5)
    async def daily_sale_check(self):
        try:
            time_now_est = datetime.datetime.now(tz.gettz('America/New_York'))
            cheapshark_link = "https://www.cheapshark.com/redirect?dealID="
            deals = self.bot.get_channel(self.deals_channel)
            historical_low_message = ""
            sale_message = ""

            # Check for game sales every day at 2 PM EST
            if time_now_est.hour >= 14 and self.daily_checked is False:
                id_list = self.dbhandler.execute("SELECT DISTINCT steam_app_id FROM game_tracker").fetchall()

                for app_id in id_list:
                    deal_id, title, sale_price, normal_price, savings, is_on_sale, store_name = game_lookup(str(app_id["steam_app_id"]))
                    db_is_on_sale_cur = self.dbhandler.execute("SELECT is_on_sale FROM game_tracker WHERE steam_app_id = ?", (app_id["steam_app_id"],)).fetchone()
                    db_is_on_sale = db_is_on_sale_cur["is_on_sale"]
                    db_lowest_price_cur = self.dbhandler.execute("SELECT lowest_price FROM game_tracker WHERE steam_app_id = ?", (app_id["steam_app_id"],)).fetchone()
                    db_lowest_price = db_lowest_price_cur["lowest_price"]
                    db_user_cur = self.dbhandler.execute(
                        "SELECT user FROM game_tracker WHERE steam_app_id = ?",(app_id["steam_app_id"],)).fetchall()

                    # Grab all users that are tracking this game
                    db_user_list = []
                    for user in db_user_cur:
                        db_user_list = db_user_list + [user["user"]]
                    mentions = ""

                    no_sales = sum(is_on_sale)  # If there are no sales from game lookup, sum will equal zero
                    # Check for game sales, if any
                    if db_is_on_sale == 1 and no_sales == 0:
                        self.dbhandler.execute("UPDATE game_tracker SET is_on_sale = 0 WHERE steam_app_id = ?",
                                               (app_id["steam_app_id"],))
                    elif db_is_on_sale == 0 and no_sales == 0:
                        pass
                    else:
                        # Find the game's lowest sale price from all stores from the game lookup and also grab i's index
                        store_index = None
                        lowest_price = 300.0
                        for i in range(0, len(sale_price)):
                            float_sale_price = float(sale_price[i])
                            if float_sale_price <= lowest_price:
                                lowest_price = float_sale_price
                                store_index = i

                        if is_on_sale[store_index] == 1:
                            if lowest_price < db_lowest_price:
                                historical_low_message = historical_low_message + f"# **{title[store_index]}** has hit a NEW all time low at `${lowest_price}` on [{store_name[store_index]}](<{cheapshark_link}{deal_id[store_index]}>) ~~${normal_price[store_index]}~~ | `-{savings[store_index]}% OFF`!\n"
                                self.dbhandler.execute("UPDATE game_tracker SET lowest_price = ? WHERE steam_app_id = ?",
                                                       (lowest_price, app_id["steam_app_id"],))
                                self.dbhandler.commit()
                                # todo: iterate over mentions list
                                mentions = ""
                            # If game's lowest price is within 15% of historical database low
                            elif lowest_price <= (db_lowest_price * 1.15):
                                sale_message = sale_message + f"### **{title[store_index]}** is on sale at `${sale_price[store_index]}` on [{store_name[store_index]}](<{cheapshark_link}{deal_id[store_index]}>) ~~${normal_price[store_index]}~~ | `-{savings[store_index]}% OFF`!\n"
                            self.dbhandler.execute("UPDATE game_tracker SET is_on_sale = 1 WHERE steam_app_id = ?", (app_id["steam_app_id"],))
                            self.dbhandler.commit()

                self.daily_checked = True
                await deals.send(historical_low_message + sale_message)

        except Exception as e:
            print(e)

    # todo: Function that resets the daily_checked variable

    @commands.hybrid_command(name="game_deals", description="View or add tracked game deals")
    @app_commands.guilds(swancord)
    async def ask(self, ctx: commands.Context):
        user = str(ctx.message.author)
        user_id = ctx.message.author.id
        # We create the view and assign it to a variable so we can wait for it later.
        view = GameDealHub(user, user_id)
        await ctx.send('Please select an option:', view=view, ephemeral=True)
        # Wait for the View to stop listening for input...
        await view.wait()


# Main Menu View that returns from slash command
class GameDealHub(discord.ui.View):
    def __init__(self, user, user_id):
        super().__init__()
        self.user = user
        self.user_id = user_id

    @discord.ui.button(label="View Tracked Games", style=discord.ButtonStyle.green)
    async def view_tracked_games(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = DropdownView(self.user, self.user_id)
        await interaction.response.send_message(f"Greetings **{self.user}**, select from your list of tracked games:",
                                                view=view, ephemeral=True)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Lookup/Track Game', style=discord.ButtonStyle.red)
    async def lookup_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GameLookupModal(self.user, self.user_id))
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
    def __init__(self, user, user_id):
        super().__init__()
        self.user = user
        self.user_id = user_id

        # Adds the dropdown to our view object.
        self.add_item(Dropdown(self.user, self.user_id))


class Dropdown(discord.ui.Select):
    def __init__(self, user, user_id):
        self.user = user
        self.user_id = user_id
        self.dbhandler = database.dbhandler()
        games = self.dbhandler.execute("SELECT title, steam_app_id FROM game_tracker WHERE user = ? LIMIT 25", (self.user,))
        game_list = games.fetchall()
        options = []
        for game in game_list:
            options = options + [
                discord.SelectOption(label=game["steam_app_id"], description=game["title"])
            ]

        super().__init__(placeholder='Select Game', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        app_id = self.values[0]
        dropdown_game_lookup = GameLookupModal(self.user, self.user_id).on_submit(interaction, app_id)
        await dropdown_game_lookup


# Modal popup on "Lookup/Track Game" Button
class GameLookupModal(discord.ui.Modal, title="Game Lookup"):
    def __init__(self, user, user_id):
        self.user = user
        self.user_id = user_id
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
    async def on_submit(self, interaction: discord.Interaction, app_id=""):
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

        deal_id, title, sale_price, normal_price, savings, is_on_sale, store_name = game_lookup(app_id)

        # Map stores with their respective sale price to sort stores by lowest price for lookup response message
        store_sales = dict(map(lambda m, n: (m, n), store_name, sale_price))
        sorted_store_sales = sorted(store_sales.items(), key=lambda x: x[1])
        print(store_sales)
        print(sorted_store_sales)
        is_on_sale_check = 0
        lowest_price = 300.0

        for i in range(0, len(store_name)):
            float_sale_price = float(sale_price[i])
            if float_sale_price <= lowest_price:
                lowest_price = float_sale_price

        on_sale_stores = ""

        for i in range(0, len(store_name)):
            if is_on_sale[i] == 1:
                # todo: check if character limit will reach 2000. If so, stop adding stores. Output warning of more stores available on cheapshark website.
                on_sale_stores = (
                        on_sale_stores +
                        f"# [{store_name[i]}](<{cheapshark_link}{deal_id[i]}>) | **${sale_price[i]}**\n"
                        f"### ~~${normal_price[i]}~~ | `-{savings[i]}% OFF`\n"
                )
                is_on_sale_check = 1

        response_message = (f"# __{title[0]}__\n\n" + on_sale_stores)
        print(response_message)

        view = ViewOnLookup(app_id, is_on_sale_check, lowest_price, self.user, self.user_id, title[0], response_message)
        await interaction.response.send_message(response_message +
                                                "Select from the following options:\n",
                                                view=view, ephemeral=True)
        # Wait for the View to stop listening for input...
        await view.wait()

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)


# Track Game Button after Game Lookup returns successful
class ViewOnLookup(discord.ui.View):
    def __init__(self, app_id, is_on_sale, lowest_price, user, user_id, title, response):
        super().__init__()
        self.dbhandler = database.dbhandler()
        self.app_id = app_id
        self.is_on_sale = is_on_sale
        self.lowest_price = float(lowest_price)
        self.user = user
        self.user_id = user_id
        self.title = title
        self.response = response

    @discord.ui.button(label="Track Game", style=discord.ButtonStyle.green)
    async def track_game_on_lookup(self, interaction: discord.Interaction, button: discord.ui.Button):
        id_column = self.dbhandler.execute("SELECT steam_app_id FROM game_tracker WHERE user = ?", (self.user,))
        id_list = id_column.fetchall()
        # Check if 25-game limit was reached
        if len(id_list) > 25:
            await interaction.response.send_message("Sorry, you cannot track more than 25 games. "
                                                    "Try removing some from your tracked list.", ephemeral=True)
            return
        # Check if entry is already in database
        for i in id_list:
            if self.app_id == str(i["steam_app_id"]):
                await interaction.response.send_message("This game is already being tracked! Please try another game.", ephemeral=True)
                return

        self.dbhandler.execute("INSERT INTO game_tracker VALUES(?,?,?,?,?,?)",
                               (self.app_id, self.is_on_sale, self.lowest_price, self.user, self.user_id, self.title))
        await interaction.response.send_message('This game is now being tracked. '
                                                'You will be notified when it goes on sale again!', ephemeral=True)
        self.dbhandler.commit()
        self.stop()

    @discord.ui.button(label="Post Results", style=discord.ButtonStyle.grey)
    async def post_results_on_lookup(self, interaction: discord.Interaction, button:discord.ui.Button):
        await interaction.response.send_message(self.response)
        self.stop()

    @discord.ui.button(label="Remove Game", style=discord.ButtonStyle.red)
    async def remove_game_on_lookup(self, interaction: discord.Interaction, button:discord.ui.Button):
        # Check for entry in database
        id_column = self.dbhandler.execute("SELECT steam_app_id FROM game_tracker WHERE user = ?", (self.user,))
        id_list = id_column.fetchall()
        for i in id_list:
            if self.app_id == str(i["steam_app_id"]):
                self.dbhandler.execute("DELETE FROM game_tracker WHERE steam_app_id = ?", (int(self.app_id),))
                self.dbhandler.commit()
                await interaction.response.send_message(
                    "This game will be removed from the tracker and you will no longer be notified!", ephemeral=True)
                self.stop()
            else:
                await interaction.response.send_message(
                    "This game does not exist in your tracking list. Try adding it first!", ephemeral=True)
                self.stop()


async def setup(bot):
    await bot.add_cog(GameDealCog(bot=bot))
