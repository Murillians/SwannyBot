import asyncio
import logging
import shutil
import sqlite3
import time
from datetime import datetime
from datetime import timedelta
from os.path import exists
from sys import platform


class dbhandler():
    databaseFile = ""
    if platform == "linux":
        databaseFile = "/config/swannybot.db"
        logging.info("LINUX detected, loading database from /config/swannybot.db")
    else:
        databaseFile = "swannybot.db"
        logging.info("Windows/Other OS detected, loading database from /swannybot.db")

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
            cur.execute(" SELECT count(*) FROM sqlite_master WHERE type='table' AND name='TEST' ")
            row = cur.fetchone()
            if row[0] == 1:
                cur.execute(" SELECT * FROM TEST ")
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
            cur.execute("CREATE TABLE IF NOT EXISTS Special(count int, id int)")
        except:
            print("An Unknown Error has occurred with the database, rebuilding")
            shutil.copy(self.databaseFile, self.databaseFile + ".prerebuild")
            self.initialDBSetup()

    def initialDBSetup(self):
        cur = self.conn.cursor()
        cur.execute("CREATE TABLE TEST(value TEXT)")
        cur.execute("CREATE TABLE streamers(TwitchUserID TEXT, LastStreamTime TEXT )")
        cur.execute("CREATE TABLE guildStreamers(GuildID TEXT, TwitchUserID TEXT)")
        cur.execute("CREATE TABLE guildChannels(GuildID TEXT, ChannelID TEXT)")
        cur.execute("CREATE TABLE Special(count int, id int)")
        cur.execute("CREATE TABLE game_tracker(steam_app_id INT, user_id INT, is_on_sale BOOL, lowest_price DECIMAL(10,2))")
        # self.cur.execute("CREATE TABLE birthdays (GuildID TEXT, UserID TEXT, birthday TEXT)")
        self.conn.commit()
        cur.execute("INSERT INTO TEST values ('swannybot')")
        self.conn.commit()
        self.conn.close()
        logging.debug("was able to successfully initialize database")

    # Executes a DB query, usage is execute(query, data), e.g.
    #   dbhandler.execute("SELECT * FROM streamers WHERE TwitchUserID=?, swanny")
    # Note: If doing a single select the correct format is
    #   dbhandler.execute(select * from streamers where TwitchUserID=?, (data,))
    #   The trailing comma in the data parameter is necessary for single values
    def execute(self, query, data=None):
        cur = self.conn.cursor()
        if data:
            cur.execute(query, data)
        else:
            cur.execute(query)
        return cur

    # Inserts data in the form of a dictionary into a table
    def insert(self, table_name, data=None):
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        sql = 'INSERT INTO {} ({}) VALUES ({})'.format(table_name, columns, placeholders)
        self.execute(sql, data.values())
        self.conn.commit()

    # For manually committing to DB
    def commit(self):
        self.conn.commit()