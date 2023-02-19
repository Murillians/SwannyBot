import yt_dlp
from discord.ext import commands
from discord import File
import os.path
import ffmpeg
class video_cog(commands.Cog):
    ctxTemp = None


    def error_handler(d):
        if d['status']=='error':
            video_cog.ctxTemp.channel.send("Was unable to download this file, this link may be unsupported! Double check it!")
    #optimal format for discord IF supported by site
    ydl_opts = {
        'progress_hooks': [error_handler],
        'format': 'best[vcodec!=h265][ext=mp4]',
        'outtmpl': '%(id)s.mp4'
    }
    #overall optimal download for transcoding
    ydl_opts_transcode= {"format" : "bv*+ba*", 'outtmpl': 'temp'}
    #todo: make download reply to calling message
    @commands.command(name="download", aliases=["dl"])
    async def download(self, ctx: commands.Context,arg1):
        video_cog.ctxTemp=ctx
        ydl = yt_dlp.YoutubeDL(self.ydl_opts)
        link = str(arg1)
        info = None
        remux=False
        try:
            info = ydl.extract_info(link, download=False)
        except BaseException:
            print("Available format not found, forcing a transcode")
            ydl=yt_dlp.YoutubeDL(self.ydl_opts_transcode) #remake downloader to grab best quality
            remux=True
        if remux is not True:
            try:
                error_code = ydl.download(link)
            except BaseException or error_code:
                await ctx.channel.send("Was unable to download this file, double check your link and try again")
                return
        if remux is True:
            try:
                info = ydl.extract_info(link)
                error_code = ydl.download(link)
            except BaseException or error_code:
                await ctx.channel.send("Was unable to download this file, double check your link and try again")
                return
            inputfile=("temp"+"."+info["ext"])
            ffmpeg.input(inputfile).output((info["id"]+"transcode"+".mp4"),vcodec='libx264', acodec="aac").run()
            os.remove("temp"+"."+info["ext"])

        filename=info["id"]
        filesize=os.path.getsize("%s.mp4" % filename)
        video_file = open("%s.mp4" % filename, 'rb')
        if filesize > 8000000:
            await ctx.channel.send("File is too large, unable to embed")
            os.remove("%s.mp4" % filename)
        else:
            await ctx.channel.send(file=File(video_file))
        video_file.close()
        os.remove("%s.mp4" % filename)
        try:
            os.remove(info["id"]+"transcode"+".mp4")
        except OSError:
            pass
