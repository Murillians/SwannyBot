import sqlite3
import logging
from os.path import exists
import shutil
from discord.ext import commands
import logging
import shutil
import sqlite3
from os.path import exists
from discord.ext import commands

import swannybottokens


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
        self.TwitchEndpoint='https://api.twitch.tv/helix/streams?user_login='
        self.TwitchClientID=swannybottokens.TwitchClientID
        self.TwitchSecret=swannybottokens.TwitchSecret

    def __del__(self):
        self.db.close()

    # Add Channel Function
    @commands.command(name="add_twitch_channel", help="Adds new channel to list of channels this server will be notified of")
    async def addNewChannel(self,ctx,*args):

    #def removeChannel(self):

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
