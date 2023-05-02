import logging
import os.path
import ffmpeg
import yt_dlp
from discord import File
from discord.ext import commands


class video_cog(commands.Cog):
    #used in ytdlp error handler
    ctxTemp = None

    def error_handler(d):
        if d['status'] == 'error':
            video_cog.ctxTemp.channel.send(
                "Was unable to download this file, this link may be unsupported! Double check it!")

    # optimal format for discord IF supported by site
    ydl_opts = {
        'progress_hooks': [error_handler],
        'format': 'best[vcodec!=h265][ext=mp4]',
        'outtmpl': '%(id)s.mp4'
    }
    # overall optimal download for transcoding
    ydl_opts_transcode = {"format": "bv*+ba*", 'outtmpl': 'temp'}

    @commands.command(name="download", aliases=["dl"])
    async def download(self, ctx: commands.Context, arg1):
        # attempt a remove if didnt delete incorrectly last time
        try:
            os.remove("temp.mp4")
        except:
            pass
        self.ctxTemp=ctx
        ydl = yt_dlp.YoutubeDL(self.ydl_opts)
        link = str(arg1)
        info = None
        remux = False
        try:
            info = ydl.extract_info(link, download=False)
        except BaseException:
            logging.info("Available format not found, forcing a transcode")
            ydl = yt_dlp.YoutubeDL(self.ydl_opts_transcode)  # remake downloader to grab best quality
            remux = True
        if remux is not True:
            try:
                error_code = ydl.download(link)
            except BaseException or error_code:
                await ctx.reply("Was unable to download this file, double check your link and try again")
                return
        if remux is True:
            try:
                info = ydl.extract_info(link)
                error_code = ydl.download(link)
            except BaseException or error_code:
                await ctx.reply("Was unable to download this file, double check your link and try again")
                return
            # if the file is too big before the transcode, don't even bother with the transcode
            inputfile = ("temp." + info['ext'])
            if os.path.getsize(inputfile) > 25000000:
                await ctx.reply("File is too large, unable to embed")
                os.remove(inputfile)
            # actual transcoding function
            ffmpeg.input(inputfile).output((info["id"] + ".mp4"), vcodec='libx264', acodec="aac").run()
            # delete the temporary downloded file
            os.remove("temp" + "." + info["ext"])

        filename = info["id"]
        filesize = os.path.getsize("%s.mp4" % filename)
        try:
            video_file = open("%s.mp4" % filename, 'rb')
        except:
            ctx.reply("Unable to attach file")
        if filesize > 8000000:
            await ctx.reply("File is too large, unable to embed")
            os.remove("%s.mp4" % filename)
        else:
            await ctx.reply(file=File(video_file))
        video_file.close()
        os.remove("%s.mp4" % filename)
        try:
            os.remove(info["id"] + "transcode" + ".mp4")
        except OSError:
            pass
        try:
            os.remove("temp")
        except OSError:
            pass
