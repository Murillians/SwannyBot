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
        'outtmpl': '%(id)s.%(ext)s'
    }
    # overall optimal download for transcoding
    ydl_opts_transcode = {"format": "bv*+ba*",
                          'outtmpl': '%(id)s.%(ext)s'
                          }


    @commands.command(name="download", aliases=["dl"])
    async def download(self, ctx: commands.Context, arg1):
        ydl = yt_dlp.YoutubeDL(self.ydl_opts)
        link = str(arg1)
        info = None
        remux = False
        inputfile=""
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
            except BaseException or error_code:
                await ctx.reply("Was unable to download this file, double check your link and try again")
                return
        if remux is True:
            try:
                ydl = yt_dlp.YoutubeDL(self.ydl_opts_transcode)  # remake downloader to grab best quality
                info = ydl.extract_info(link,download = False)
                error_code = ydl.download(link)
            except BaseException or error_code:
                await ctx.reply("Was unable to download this file, double check your link and try again")
                return
            #reget file info, may have downloaded w/ different extension
            inputfile = (info['id'] + "." + info['ext'])
            # if the file is too big before transcode, don't even bother with transcode
            if os.path.getsize(inputfile) > 25000000:
                await ctx.reply("File is too large, unable to embed")
                os.remove(inputfile)
            # actual transcoding function
            ffmpeg.input(inputfile).output((info["id"] + ".transcode.mp4"), vcodec='libx264', acodec="aac").run()
            # delete the temporary downloded file
            os.remove(inputfile)
            #file being sent to discord is now %id.transcode.mp4
            inputfile=info['id'] + ".transcode.mp4"
        try:
            filesize = os.path.getsize(inputfile)
            video_file = open(inputfile, 'rb')
            if filesize > 25000000:
                await ctx.reply("File is too large, unable to embed")
            else:
                await ctx.reply(file=File(video_file))
            video_file.close()
            os.remove(inputfile)
        except:
            await ctx.reply("Unable to attach file")
        #used for deleting videos we didnt want (usually twitter quote videos where OT & QRT both have videos)
        try:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            files = os.listdir(dir_path)
            for item in files:
                if item.endswith(".mp4"):
                    os.remove(os.path.join(dir_path, item))

        except OSError:
            pass
async def setup(bot):
    await bot.add_cog(video_cog(bot=bot))