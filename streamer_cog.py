import asyncio
import logging
import shutil
import sqlite3
from datetime import datetime
from datetime import timedelta
import dateutil.parser
import dateutil.tz
from os.path import exists
import discord
import requests
from discord.ext import commands
from discord.ext import tasks

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
        self.bot=bot

        # make db backup if exists, for testing
        if exists('streamer.db'):
            shutil.copy('streamer.db', 'streamer.db.backup')

        self.db = sqlite3.connect('streamer.db')
        self.db.row_factory = sqlite3.Row
        logging.info("was able to open database file, checking for integrity")
        self.cur = self.db.cursor()
        # run self check once database opens
        self.selfCheck()
        self.TwitchClientID = swannybottokens.TwitchClientID
        self.TwitchSecret = swannybottokens.TwitchSecret
        #begin checking channels
        #todo: make wait until after everything above goes
        self.checkChannels.start()

        def __del__(self):
            self.db.close()



    @tasks.loop(seconds=60)
    async def checkChannels(self):
        await asyncio.sleep(1)
        for row in self.cur.execute("Select * from Streamers"):
            print("Querying twitch for info on "+row["TwitchUserID"])
            self.TwitchEndpoint = 'https://api.twitch.tv/helix/streams?user_id='
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
            # TODO break out into generic twitch access function that takes endpoint target (/helix/?????)
            stream = requests.get(self.TwitchEndpoint + row["TwitchUserID"], headers=headers, allow_redirects=True, timeout=1)
            streamData = stream.json()
            #stop running the loop if they aren't live
            if len(streamData["data"])==0:
                continue
            streamData=streamData["data"][0]
            fixedTime = streamData["started_at"]
            fixedTime = fixedTime[:-1]
            fixedTime= datetime.fromisoformat(fixedTime)
            #twitch returns a ISO 8601 timestamp w/ 'Z' at the end for timezone, so strip that out cause python freaks
            lastStarted=datetime.fromisoformat(row["LastStreamTime"])
            lastStarted=lastStarted+timedelta(hours=12)
            if (streamData["type"]=="live") and (fixedTime > lastStarted):
                print(streamData)
                print(streamData["user_name"] + " is live! ")
                #todo parse discords to update/send update message
                for row in self.cur.execute("select * from guildStreamers left join guildChannels gC on guildStreamers.GuildID = gC.GuildID where TwitchUserID=?",(row["TwitchUserID"],)):
                    destChannel= self.bot.get_channel(int(row["TwitchUserID"]))
                    richEmbed = discord.Embed(
                        title=streamData["user_login"] + " is live! Playing "+streamData["game_name"]+"!",
                        url=('https://www.twitch.tv/' + streamData["user_login"])
                    ).set_image(url=streamData["thumbnail_url"]).set_thumbnail(
                        url=streamData["thumbnail_url"])
                    await destChannel.send(embed=richEmbed)
                self.db.execute('''update streamers set LastStreamTime=datetime('now') WHERE TwitchUserID=?''',(streamData["user_id"],))
                self.db.commit()
    @checkChannels.before_loop
    async def before_checkChannels(self):
        await self.bot.wait_until_ready()

    # Add Channel Function
    @commands.command(name="add_twitch_channel",
                      help="Adds new channel to list of channels this server will be notified of")
    async def addNewChannel(self, ctx, *args):
        guild = ctx.guild.id
        newchannel = args[0]
        logging.debug("Guild ID: ", guild, " wants to follow ", newchannel)
        twitchChannelInfo = self.getTwitchChannel(newchannel)
        if twitchChannelInfo == False:
            await ctx.send("Not a valid twitch channel! Check your spelling!")
            return
        self.cur.execute("INSERT into Streamers VALUES(?,?)",(twitchChannelInfo.id,datetime.min))
        self.cur.execute("INSERT into guildStreamers (GuildID,TwitchUserID) values (?,?) ",(guild,twitchChannelInfo.id))
        self.db.commit()
        richEmbed = discord.Embed(
                title='Successfully added ' + twitchChannelInfo.display_name + " to your list of subscribed twitch channels!",
                url=('https://www.twitch.tv/' + twitchChannelInfo.user_login)
            ).set_image(url=twitchChannelInfo.profile_image_url).set_thumbnail(url=twitchChannelInfo.profile_image_url)
        await ctx.send(embed=richEmbed)

    # Add Channel Function
    @commands.command(name="set_stream_notifications",
                      help="Sets current channel to receive stream notifications")
    async def setStreamNotifications(self, ctx):
        guild = ctx.guild.id
        currentChannel = ctx.channel.id
        #TODO:fix
        self.cur.execute("Select * From guildChannels where GuildID=?", (guild,))
        row = self.cur.fetchone()
        if row==None or len(row) == 0:
            self.cur.execute('''INSERT INTO guildChannels(GuildID,ChannelID) VALUES(?,?)''',(guild,currentChannel))
            self.db.commit()
            await ctx.send("Successfully made this channel the default for stream notifications!")
            return
        #changed self.bot to discord.Client
        await ctx.send("Warning, this server currently receives notifications in " +discord.Client.get_channel(int(row["ChannelID"])).mention)
        print("test")
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
        #todo: possibly change table datatypes to correlate w/ expected values?
        self.cur.execute('''create table TEST(value text)''')
        self.cur.execute('''create table streamers(ChannelID text, LastStreamTime text )''')
        self.cur.execute('''create table guildStreamers(GuildID text, TwitchUserID text)''')
        self.cur.execute('''create table guildChannels(GuildID text, ChannelID text)''')
        self.db.commit()
        self.cur.execute('''insert into TEST values ('swannybot')''')
        self.db.commit()
        self.db.close()
        logging.debug("was able to successfully initialize database")

    def getTwitchChannel(self, channel):
        # set twitch endpoint to get user profile
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
        # TODO break out into generic twitch access function that takes endpoint target (/helix/?????)
        stream = requests.get(self.TwitchEndpoint + channel, headers=headers, allow_redirects=True, timeout=1)
        userData = stream.json()
        if (len(userData["data"]) == 0):
            return False
        else:
            returnVal = channelInfo()
            returnVal.parseUser(userData)
            return returnVal