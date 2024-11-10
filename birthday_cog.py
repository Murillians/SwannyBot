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


# Helper for date input validation
def is_valid_date(month: int, day: int) -> bool:
    try:
        # Attempt to create a date with the given month and day for a common leap year
        datetime.datetime(year=2000, month=month, day=day)
        return True
    except ValueError:
        # If ValueError is raised, month or day is invalid
        return False


# Helper for quote retrieval when birthday is announced
def quote_lookup():
    api_url = "https://zenquotes.io/api/random/"

    payload = {}
    headers = {}

    response = requests.request("GET", api_url, headers=headers, data=payload)
    if response.status_code == 200:

        parsed = json.loads(response.text)
        # Pretty Print JSON Formatter
        # print(json.dumps(parsed, indent=3))

        result = response.json()
        quote = result[0]['q']
        author = result[0]['a']

        return quote, author


# Main Birthday Cog that checks daily for birthdays
class BirthdayCog(commands.Cog, name="BirthdayCog"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.dbhandler = database.dbhandler()
        self.check_on_schedule.start()
    #todo: finalize when done
    swancord_general = 1154762810987921438  # Currently bawt-spam, change later
    boyscord_general = 570735067580727309

    @commands.command(name="birthdaytest")
    async def birthdaytest(self, ctx):
        await self.daily_birthday_check()

    # Check database entries for birthday.
    async def daily_birthday_check(self):
        today = datetime.date.today()
        this_month = today.month
        this_day = today.day

        db_user_id_cur = self.dbhandler.execute("SELECT user_id FROM birthdays WHERE month = ? AND day = ?",
                                                (this_month, this_day))

        # Grab all users who have a birthday today
        if db_user_id_cur:
            for i in db_user_id_cur:
                quote, author = quote_lookup()
                user_id = i['user_id']
                db_user_cur = self.dbhandler.execute(f"SELECT user FROM birthdays WHERE user_id = {user_id}")
                db_guild_cur = self.dbhandler.execute(f"SELECT guild_id FROM birthdays WHERE user_id = {user_id}")
                user = db_user_cur[0]['user']
                guild = int(db_guild_cur[0]['guild_id'])
                general_channel = self.bot.get_channel(self.swancord_general)
                guild_name = self.bot.get_guild(swannybottokens.swancord).name

                # If bot is in more servers, below will need a small refactor
                if guild == swannybottokens.jesuscord:
                    general_channel = self.bot.get_channel(self.boyscord_general)
                    guild_name = self.bot.get_guild(swannybottokens.jesuscord).name

                await general_channel.send(
                    f"""
🎉🎊🎈🎂 Today is <@{user_id}>'s birthday! 🎂🎈🎊🎉
🥳 Everyone, please join me in singing happy birthday to **{user}**!

*Happy birthday to you!* 🎶
*Happy birthday to you!* 🎵
*Happy birthday dear **{user}**!* 💝
*Happy birthday to you!* 🎶
            
😄 And for your special day, **{user}**, here is an inspirational quote I found just for you:
## "{quote}"
    ### -- {author}

😊 **Have a great birthday!** 

*Love,*

    **Swanny Bot** ❤️
        💖❤️ **and all of your friends of the {guild_name} server!** ❤️💖
                    """)

    # Check for birthdays at midnight EST
    @tasks.loop(time=datetime.time(hour=0, minute=0, second=10, tzinfo=tz.gettz('America/New_York')))
    async def check_on_schedule(self):
        await self.daily_birthday_check()

    @commands.hybrid_command(name="birthdays", description="View or add a birthday.")
    @app_commands.guilds(swancord, boyscord)
    async def ask(self, ctx: commands.Context):
        user = str(ctx.message.author)
        user_id = ctx.message.author.id
        guild_id = ctx.message.guild.id
        view = BirthdayMenu(user, user_id, guild_id)
        await ctx.send('Please select an option:', view=view, ephemeral=True)
        await view.wait()


# Main Menu View that returns buttons from slash command
class BirthdayMenu(discord.ui.View):
    def __init__(self, user, user_id, guild_id):
        super().__init__()
        self.user = user
        self.user_id = user_id
        self.guild_id = guild_id
        self.dbhandler = database.dbhandler()

    @discord.ui.button(label='See Birthdays', style=discord.ButtonStyle.blurple)
    async def see_birthdays(self, interaction: discord.Interaction, button: discord.ui.Button):
        db_table_cur = self.dbhandler.execute(f"SELECT * FROM birthdays WHERE guild_id = {self.guild_id}")
        if db_table_cur:
            return_message = ""

            for i in db_table_cur:
                user = i['user']
                month = i['month']
                day = i['day']

                return_message = return_message + f"**{user}**, {month}/{day}\n"

            await interaction.response.send_message(return_message, ephemeral=True)
        else:
            await interaction.response.send_message("There are no birthdays recorded on this server. "
                                                    "Be the first to add one!", ephemeral=True)

    @discord.ui.button(label='Add Birthday', style=discord.ButtonStyle.green)
    async def add_birthday(self, interaction: discord.Interaction, button: discord.ui.Button):
        db_user_id_cur = self.dbhandler.execute(f"SELECT * FROM birthdays WHERE user_id = {self.user_id} AND guild_id = {self.guild_id}")
        if db_user_id_cur:
            await interaction.response.send_message("Your birthday was already added to this server. "
                                                    "No need to add a new birthday.", ephemeral=True)
        else:
            await interaction.response.send_modal(AddBirthdayModal(self.user, self.user_id, self.guild_id))
        self.stop()

    @discord.ui.button(label='Remove Birthday', style=discord.ButtonStyle.red)
    async def remove_birthday(self, interaction: discord.Interaction, button: discord.ui.Button):
        db_user_id_cur = self.dbhandler.execute(f"SELECT * FROM birthdays WHERE user_id = {self.user_id}")
        if db_user_id_cur:
            for i in db_user_id_cur:
                self.dbhandler.execute(f"DELETE FROM birthdays WHERE user_id = {i['user_id']}")
            await interaction.response.send_message("Your birthday was removed and will no longer be announced!",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message("Your birthday was not found. Add a birthday to remove it.",
                                                    ephemeral=True)
        self.stop()

    @discord.ui.button(label='Help', style=discord.ButtonStyle.grey)
    async def birthday_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            """
### What is `/birthdays`?
This application command will record your birthday month and day and send a special announcement via your server's general channel!

### How do I use `/birthdays`?
**See Birthdays**
This will show all the recorded birthdays on this server.
- Your birthday month and day is only seen by users of the same server in our secure database.

**Add Birthday**
With this, you can add your birthday month and day (MM/DD format) to this server.
- Placing a 0 in front of your month or day is *optional*.
- You can not add birthdays for other users. Only users that use the slash command can add their own birthdays.

**Remove Birthday**
This will remove your birthday month and day from the server and your birthday will no longer be announced.
            """, ephemeral=True)
        self.stop()


# Modal popup on "Add Birthday" button
class AddBirthdayModal(discord.ui.Modal, title="Add Your Birthday (MM/DD)"):
    def __init__(self, user, user_id, guild_id):
        self.user = user
        self.user_id = user_id
        self.guild_id = guild_id
        self.dbhandler = database.dbhandler()
        super().__init__()

    # User enters month "MM"
    month = discord.ui.TextInput(
        label='Month',
        style=discord.TextStyle.short,
        placeholder='MM',
        required=True,
        max_length=2,
    )

    # User enters day "DD"
    day = discord.ui.TextInput(
        label='Day',
        style=discord.TextStyle.short,
        placeholder='DD',
        required=True,
        max_length=2,
    )

    async def on_submit(self, interaction: discord.Interaction):
        month = self.month.value
        day = self.day.value
        if month.isdigit() and day.isdigit() and is_valid_date(int(month), int(day)):
            await interaction.response.send_message(f'{self.user}, your birthday will be announced on '
                                                    f'{int(month)}/{int(day)}', ephemeral=True)
            self.dbhandler.execute("INSERT INTO birthdays VALUES (?, ?, ?, ?, ?)",
                                   (int(month), int(day), self.user, self.user_id, self.guild_id))
        else:
            await interaction.response.send_message("Sorry, you must enter a valid date! Please try again.", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)


async def setup(bot):
    await bot.add_cog(BirthdayCog(bot=bot))
