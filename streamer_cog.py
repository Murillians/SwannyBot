import discord
import sqlite3
import swannybottokens
import requests
from discord.ext import commands

class streamer_cog(commands.Cog):
    def __init__(self):
        self.db = None
        db=sqlite3.connect('streamer.db')
        self.cur=db.cursor()
        #run self check once database opens
        self.selfCheck()
    def __del__(self):
        self.db.close()
    #Add Channel Function
    #@commands.command(name="add_twitch_channel", help="Adds new channel to list of channels this server will be notified of")
    #async def addNewChannel(self,ctx,*args):

    #def removeChannel(self):

    def selfCheck(self):
        self.cur.execute('select * from TEST ')
        if (self.cur.fetchone())[0] != 'swannybot':
            self.initialDBSetup()
    def initialDBSetup(self):
        self.cur.execute('''create table TEST(value text)''')
        self.cur.execute('''insert into TEST values ('swannybot')''')
        #self.cur.execute('create table guilds(guild_id text,')
        self.cur.execute('''create table streamers(channel_id text, guild_id text,''')
        self.db.commit()

