import asyncio
import logging
import time
from datetime import datetime
from datetime import timedelta
import discord
import requests
from discord.ext import commands
from discord.ext import tasks
import database
import aiohttp
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
    cur = None


    def __init__(self, bot):
        self.bot = bot
        self.TwitchClientID = swannybottokens.TwitchClientID
        self.TwitchSecret = swannybottokens.TwitchSecret
        self.dbhandler=database.dbhandler()
        self.checkChannels.start()
        oauth = {
            'client_id': self.TwitchClientID,
            'client_secret': self.TwitchSecret,
            "grant_type": 'client_credentials'
        }
        p = requests.post('https://id.twitch.tv/oauth2/token', oauth)
        keys = p.json()
        self.headers = {
            'Client-ID': self.TwitchClientID,
            'Authorization': 'Bearer ' + keys['access_token']
        }

    @tasks.loop(seconds=120)
    async def checkChannels(self):
        self.TwitchEndpoint = 'https://api.twitch.tv/helix/streams?user_id='
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for row in self.dbhandler.execute("select * from streamers"):
                print("Querying twitch for info on " + row["TwitchUserID"])
                async with session.get(str(self.TwitchEndpoint + row["TwitchUserID"])) as response:
                    if response.status == 200:
                        streamData = await response.json()
                        # stop running the loop if they aren't live
                        if len(streamData["data"]) == 0:
                            continue
                        streamData = streamData["data"][0]
                        fixedTime = streamData["started_at"]
                        fixedTime = fixedTime[:-1]
                        fixedTime = datetime.fromisoformat(fixedTime)
                        # twitch returns a ISO 8601 timestamp w/ 'Z' at the end for timezone, so strip that out cause python freaks
                        lastStarted = datetime.fromisoformat(row["LastStreamTime"])
                        lastStarted = lastStarted + timedelta(hours=6)
                        if (streamData["type"] == "live") and (fixedTime > lastStarted):
                            #print(streamData)
                            print(streamData["user_name"] + " went live at "+str(time.time()))
                            for row in self.dbhandler.execute("select * from guildStreamers left join guildChannels gC on guildStreamers.GuildID = gC.GuildID where TwitchUserID=?",(row["TwitchUserID"],)):
                                destChannel = self.bot.get_channel(int(row["ChannelID"]))
                                richEmbed = discord.Embed(
                                    title=streamData["user_login"] + " is live! Playing " + streamData["game_name"] + "!",
                                    url=('https://www.twitch.tv/' + streamData["user_login"])
                                ).set_image(url=streamData["thumbnail_url"]).set_thumbnail(
                                    url=streamData["thumbnail_url"])
                                await destChannel.send(embed=richEmbed)
                            self.dbhandler.execute("update streamers set LastStreamTime=datetime('now') WHERE TwitchUserID=?",
                                            (streamData["user_id"],))
                            self.dbhandler.commit()



    # Add Channel Function
    @commands.command(name="add_twitch_channel",
                      help="Adds new channel to list of channels this server will be notified of")
    async def addNewChannel(self, ctx, *args):
        guild = ctx.guild.id
        newchannel = args[0]
        logging.debug("Guild ID: ", guild, " wants to follow ", newchannel)
        twitchChannelInfo = await self.getTwitchChannel(newchannel)
        if twitchChannelInfo == False:
            await ctx.send("Not a valid twitch channel! Check your spelling!")
            return
        self.dbhandler.execute("INSERT into Streamers VALUES(?,?)", (twitchChannelInfo.id, datetime.min))
        self.dbhandler.execute("INSERT into guildStreamers (GuildID,TwitchUserID) values (?,?) ",
                         (guild, twitchChannelInfo.id))
        self.dbhandler.commit()
        richEmbed = discord.Embed(
            title='Successfully added ' + twitchChannelInfo.display_name + " to your list of subscribed twitch channels!",
            url=('https://www.twitch.tv/' + twitchChannelInfo.user_login)
        ).set_image(url=twitchChannelInfo.profile_image_url).set_thumbnail(url=twitchChannelInfo.profile_image_url)
        await ctx.reply(embed=richEmbed)

    # Add Channel Function
    @commands.command(name="set_stream_notifications",
                      help="Sets current channel to receive stream notifications")
    async def setStreamNotifications(self, ctx):
        guild = ctx.guild.id
        currentChannel = ctx.channel.id
        # TODO:fix
        data = self.dbhandler.execute("Select * From guildChannels where GuildID=?", (guild,))
        row = data.fetchone()
        if row == None or len(row) == 0:
            self.dbhandler.execute('''INSERT INTO guildChannels(GuildID,ChannelID) VALUES(?,?)''', (guild, currentChannel))
            self.dbhandler.commit()
            await ctx.send("Successfully made this channel the default for stream notifications!")
            return

        # handling if server already has default notif channel
        def check(m):
            if m.content in {'y', 'Y', 'yes', 'Yes'}:
                return True
            elif m.content in {'n', 'N', 'no', 'No'}:
                return False
            else:
                return

        await ctx.send("Warning, this server currently receives notifications in " + ctx.guild.get_channel(
            int(row["ChannelID"])).mention +
                       "\n Would you like to make this channel the default for streaming notifications? (Y/N)")
        try:
            reply = await self.bot.wait_for('message', check=check, timeout=10)
            if reply:
                self.dbhandler.execute('''update guildChannels set ChannelID=? where GuildID=?''',
                                 (currentChannel, guild))
                self.dbhandler.commit()
                await ctx.send("Successfully made this channel the default for stream notifications!")
                return
            elif not reply:
                await ctx.send(
                    "OK, you\'ll keep getting notifications in " + ctx.guild.get_channel(int(row["ChannelID"])).mention)
                return
            else:
                await ctx.send("Incorrect response (its yes or no dog c\'mon")
                return
        except asyncio.TimeoutError:
            return await ctx.channel.send("Sorry, you took too long")

    #Delete Channel Function
    @commands.command(name="delete_twitch_channel", help="Remove a Twitch channel from this servers notifications")
    async def deleteTwitchChannel(self,ctx,*args):
        guild = ctx.guild.id
        newchannel = args[0]
        logging.debug("Guild ID: ", guild, " wants to remove ", newchannel)
        twitchChannelInfo = await self.getTwitchChannel(newchannel)
        if twitchChannelInfo == False:
            await ctx.send("Not a valid twitch channel! Check your spelling!")
            return
        self.dbhandler.execute("delete from guildStreamers where GuildID=(?) and TwitchUserID=(?)",
                         (guild, twitchChannelInfo.id))
        self.dbhandler.commit()
        await ctx.send('Successfully removed ' + twitchChannelInfo.display_name + " from your list of subscribed twitch channels!")
    @commands.command(name="list_twitch_channels",aliases=["twitch_list"], help="See a list of subscribed twitch channels for this server")
    async def listTwitchChannels(self,ctx):
        guild=ctx.guild.id
        channelList="This server is currently subscribed to the following twitch channels:\n"
        self.TwitchEndpoint = 'https://api.twitch.tv/helix/users?id='
        async with aiohttp.ClientSession(headers=self.headers) as session:
            rows=self.dbhandler.execute("select * from guildStreamers where GuildID=?",(guild,))
            for row in rows:
                async with session.get(str(self.TwitchEndpoint + row["TwitchUserID"])) as response:
                    if response.status == 200:
                        streamData = await response.json()
                        streamData=streamData["data"][0]
                        username=streamData["display_name"]
                        channelList+=(username+"\n")
        await ctx.reply(channelList)

    async def getTwitchChannel(self, channel):
        # set twitch endpoint to get user profile
        self.TwitchEndpoint = 'https://api.twitch.tv/helix/users?login='
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(str(self.TwitchEndpoint + channel)) as response:
                if response.status ==200:
                    userData = await response.json()
                    if (len(userData["data"]) == 0):
                        return False
                    else:
                        returnVal = channelInfo()
                        returnVal.parseUser(userData)
                        return returnVal
