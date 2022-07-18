import discord
import yt_dlp
from discord.ext import commands,tasks
from discord import File
import os.path
class video_cog(commands.Cog):
    ydl_opts = {
        'format':'best[vcodec!=h265][ext=mp4]',
        'outtmpl':'%(id)s.mp4'
    }
    @commands.command(name="download", aliases=["dl"])
    async def download(self, ctx: commands.Context,arg1):
        ydl = yt_dlp.YoutubeDL(self.ydl_opts)
        link = str(arg1)
        info = ydl.extract_info(link)
        try:
            error_code = ydl.download(link)
        except BaseException:
            await ctx.channel.send("Was unable to download this file, double check your link and try again")
            return
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

