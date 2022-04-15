import logging
import shutil
import sqlite3
from os.path import exists

import discord
import requests
from discord.ext import commands

import swannybottokens


class channelInfo():
    def __init__(self):
        self.id = None
        self.user_name = None
        self.user_login = None
        self.started_at = None
        self.game_name = None
        self.profile_image_url = None
        self.offline_image_url = None
        self.display_name = None

    # for parsing a user
    def parseUser(self, userData):
        self.id = userData["data"][0]['id']
        self.display_name = userData["data"][0]['display_name']
        self.user_login = userData["data"][0]['login']
        self.profile_image_url = userData["data"][0]['profile_image_url']
        self.offline_image_url = userData["data"][0]['offline_image_url']


class streamer_cog(commands.Cog):
    db = None
    cur = None

    def __init__(self, bot):
        # make db backup if exists, for testing
        if exists('streamer.db'):
            shutil.copy('streamer.db', 'streamer.db.backup')

        self.db = sqlite3.connect('streamer.db')
        logging.info("was able to open database file, checking for integrity")
        self.cur = self.db.cursor()
        # run self check once database opens
        self.selfCheck()
        self.TwitchClientID = swannybottokens.TwitchClientID
        self.TwitchSecret = swannybottokens.TwitchSecret
        #test = self.getTwitchChannel('syberserkr')
        def __del__(self):
            self.db.close()

    # Add Channel Function
    @commands.command(name="add_twitch_channel",
                      help="Adds new channel to list of channels this server will be notified of")
    async def addNewChannel(self, ctx, *args):
        guild = ctx.guild.id
        newchannel = args[0]
        logging.debug("Guild ID: ", guild, " wants to follow ", newchannel)
        #fix return value
        channelInfo = self.getTwitchChannel(newchannel)
        if channelInfo == False:
            await ctx.send("Not a valid twitch channel! Check your spelling!")
            return
        else:
            richEmbed = discord.Embed(
                title='Successfully added ' + channelInfo.display_name + " to your list of subscribed twitch channels!",
                url=('https://www.twitch.tv/' + channelInfo.user_login)
            ).set_image(url=channelInfo.profile_image_url).set_thumbnail(url=channelInfo.profile_image_url)
            await ctx.send(embed=richEmbed)

    def selfCheck(self):
        self.cur.execute(''' SELECT count(*) FROM sqlite_master WHERE type='table' AND name='TEST' ''')
        row = self.cur.fetchone()
        if row[0] == 1:
            self.cur.execute(''' SELECT * FROM TEST ''')
            if len(row) < 1:
                self.initialDBSetup()
            elif self.cur.fetchone()[0] != 'swannybot':
                logging.debug("Database was corrupt, rebuilding")
                self.initialDBSetup()
            else:
                logging.info("Database integrity is valid, continuing")
        else:
            logging.debug("Database file was not valid! building")
            self.initialDBSetup()

    def initialDBSetup(self):
        self.cur.execute('''create table TEST(value text)''')
        self.cur.execute('''create table streamers(ChannelID text)''')
        self.cur.execute('''create table guildStreamers(GuildID text, StreamerID text)''')
        self.cur.execute('''create table guildChannels(GuildID text, ChannelID text)''')
        self.db.commit()
        self.cur.execute('''insert into TEST values ('swannybot')''')
        self.db.commit()
        self.db.close()
        logging.debug("was able to successfully initialize database")

    def getTwitchChannel(self, channel):
        #set twitch endpoint to get user profile
        self.TwitchEndpoint = 'https://api.twitch.tv/helix/users?login='
        oauth = {
            'client_id': self.TwitchClientID,
            'client_secret': self.TwitchSecret,
            "grant_type": 'client_credentials'
        }
        p = requests.post('https://id.twitch.tv/oauth2/token', oauth)
        keys = p.json()
        headers = {
            'Client-ID': self.TwitchClientID,
            'Authorization': 'Bearer ' + keys['access_token']
        }
        #TODO break out into generic twitch access function that takes endpoint target (/helix/?????)
        stream = requests.get(self.TwitchEndpoint + channel, headers=headers, allow_redirects=True, timeout=1)
        userData = stream.json()
        if (len(userData["data"]) == 0):
            return False
        else:
            returnVal= channelInfo()
            returnVal.parseUser(userData)
            return returnVal
