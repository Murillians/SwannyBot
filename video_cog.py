import logging
import os.path
import discord
import ffmpeg
import yt_dlp
import re
from discord import File
from discord.ext import commands
from tokenize import String
from urllib.parse import urlparse


class video_cog(commands.Cog):
    #used in ytdlp error handler
    ctxTemp = None

    def error_handler(d):
        if d['status'] == 'error':
            video_cog.ctxTemp.channel.send(
                "Was unable to download this file, this link may be unsupported! Double check it!")
    wanted_sites=["youtube.com","youtu.be","reddit.com","instagram.com","facebook.com","tiktok.com","x.com"]
    # optimal format for discord IF supported by site
    ydl_opts = {
        'progress_hooks': [error_handler],
        'format':  'b[vcodec~=\'^(h264|avc)\'] / b[ext=mp4]',
        'outtmpl': '%(id)s.%(ext)s'
    }
    # overall optimal download for transcoding
    ydl_opts_transcode = {"format": "bv*+ba*",
                          'outtmpl': '%(id)s.%(ext)s'
                          }

    async def downloadVideo(self,link,filesize_limit):
        ydl = yt_dlp.YoutubeDL(self.ydl_opts)
        info = None
        remux = False
        inputfile=""
        error_code = None
        try:
            info = ydl.extract_info(link, download=False)
            # if there are subentries in the pulled json info, grab the first one as it is the desired quote tweet
            if "entries" in info:
                info=info["entries"][0]

        except BaseException:
            logging.info("Available format not found, forcing a transcode")
            remux = True
        if remux is not True:
            try:
                inputfile = (info['id'] + "." + info['ext'])
                error_code = ydl.download(link)
            except BaseException or error_code is not None:
                return "Was unable to download this file, double check your link and try again"
        if remux is True:
            try:
                ydl = yt_dlp.YoutubeDL(self.ydl_opts_transcode)  # remake downloader to grab best quality
                info = ydl.extract_info(link,download = False)
                error_code = ydl.download(link)
            except BaseException or error_code:
                return ("Was unable to download this file, double check your link and try again")

            #reget file info, may have downloaded w/ different extension
            inputfile = (info['id'] + "." + info['ext'])
            # if the file is too big before transcode, don't even bother with transcode
            if os.path.getsize(inputfile) > filesize_limit:
                return ("File is too large, unable to embed")
                os.remove(inputfile)
            # actual transcoding function
            ffmpeg.input(inputfile).output((info["id"] + ".transcode.mp4"), vcodec='libx264', acodec="aac").run()
            # delete the temporary downloded file
            os.remove(inputfile)
            #file being sent to discord is now %id.transcode.mp4
            inputfile=info['id'] + ".transcode.mp4"
        try:
            filesize = os.path.getsize(inputfile)
            if filesize > filesize_limit:
                return ("File is too large, unable to embed")
            else:
                return inputfile
            video_file.close()
            os.remove(inputfile)
        except:
            return("Unable to attach file")

    @commands.command(name="download", aliases=["dl"])
    async def downloadCommand(self, ctx: commands.Context):
        # Split message up via spaces and parse for link
        link = ""
        split_message = ctx.message.content.split()
        for i in split_message:
            if i.startswith('https://'):
                link = i
        video = await self.downloadVideo(link, ctx.filesize_limit)
        if video is String:
            await ctx.reply(video)
        elif video is File:
            video_file = open(video, 'rb')
            await ctx.reply(file=File(video_file))
            video_file.close()
            os.remove(video)
        else:
            await ctx.reply("Undefined Error, sorry!")

    @commands.Cog.listener('on_message')
    async def downloadVideoOnMessage(self,message: discord.Message):
        if message.author.bot:
            return
        if len(re.findall(r"^!dl",message.content)) > 0:
            return
        link = None
        tld= None
        video = None
        #split_message = message.content.split()
        url = re.findall(r"(https?://\S+)", message.content)
        if  len(url) > 0:
            link = urlparse(url[0]).netloc
            tld = re.sub(r"^www\.","",link)
        else:
            return
        if tld not in self.wanted_sites:
            return
        if link is not None:
            video = await self.downloadVideo(url[0], message.guild.filesize_limit)
            if ".mp4" in video:
                video_file = open(video, 'rb')
                await message.reply(file=File(video_file))
                video_file.close()
                os.remove(video)
            elif type(video) is String:
                await message.reply(video)
            else:
                await message.reply("Undefined error, sorry!")
async def setup(bot):
    await bot.add_cog(video_cog(bot=bot))