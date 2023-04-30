import asyncio
import logging
import shutil
import sqlite3
import time
from datetime import datetime
from datetime import timedelta
from os.path import exists


class dbhandler():
    databaseFile = "swannybot.db"
    def __init__(self):
        self.conn = None
        self.connect()

    def __del__(self):
        self.conn.close()
    def connect(self):
        # make db backup if exists, for testing
        if exists(self.databaseFile):
            shutil.copy(self.databaseFile, self.databaseFile + ".backup")
        self.conn = sqlite3.connect(self.databaseFile)
        logging.info("was able to open database file, checking for integrity")
        self.selfCheck()
        logging.info("self check completed successfully")
        self.conn.row_factory=self.dict_factory

    def dict_factory(self, cursor, row):
        """ Used to return rows as dictionary"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    def selfCheck(self):
        cur = self.conn.cursor()
        try:
            cur.execute(''' SELECT count(*) FROM sqlite_master WHERE type='table' AND name='TEST' ''')
            row = cur.fetchone()
            if row[0] == 1:
                cur.execute(''' SELECT * FROM TEST ''')
                if len(row) < 1:
                    self.initialDBSetup()
                elif cur.fetchone()[0] != 'swannybot':
                    logging.debug("Database was corrupt, rebuilding")
                    self.initialDBSetup()
                else:
                    logging.info("Database integrity is valid, continuing")
            else:
                logging.debug("Database file was not valid! building")
                self.initialDBSetup()
        except:
            print("An Unknown Error has occurred with the database, rebuilding")
            shutil.copy(self.databaseFile, self.databaseFile + ".prerebuild")
            self.initialDBSetup()

    def initialDBSetup(self):
        cur = self.conn.cursor()
        cur.execute('''create table TEST(value text)''')
        cur.execute('''create table streamers(TwitchUserID text, LastStreamTime text )''')
        cur.execute('''create table guildStreamers(GuildID text, TwitchUserID text)''')
        cur.execute('''create table guildChannels(GuildID text, ChannelID text)''')
        "self.cur.execute('''create table birthdays (GuildID text, UserID text, birthday text)''')"
        self.conn.commit()
        cur.execute('''insert into TEST values ('swannybot')''')
        self.conn.commit()
        self.conn.close()
        logging.debug("was able to successfully initialize database")

    "Executes a DB query, usage is execute(query, data)"
    "ex: dbhandler.execute(select * from streamers where TwitchUserID=?, swanny)"
    "note if doing a single select the correct format is dbhandler.execute(select * from streamers where TwitchUserID=?, (data,))"
    "the trailing comma in the data paramater is necessary for single values"
    def execute(self,query,data=None):
        cur = self.conn.cursor()
        if (data):
            cur.execute (query,data)
        else:
            cur.execute(query)
        return cur

    """ Inserts data in the form of a dictionary into a table """
    def insert(self, tablename, data=None):
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        sql = 'INSERT INTO {} ({}) VALUES ({})'.format(tablename, columns, placeholders)
        self.execute(sql, data.values())
        self.conn.commit()
    "For manually committing to DB"
    def commit(self):
        self.conn.commit()