import asyncio
import logging
import shutil
import sqlite3
import time
from datetime import datetime
from datetime import timedelta
from os.path import exists
import discord
import requests
from discord.ext import commands
from discord.ext import tasks

import swannybottokens


class logger_cog(commands.Cog):
    db = None
    cur = None
