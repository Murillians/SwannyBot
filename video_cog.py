import asyncio
import logging
import os
import tempfile

import ffmpeg
import yt_dlp
from discord import File
from discord.ext import commands


class video_cog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    # optimal format for discord IF supported by site
    # playlist_items=1 means quote tweets only download the first (desired) video
    # outtmpl is added per call so downloads land in that call's temp directory
    ydl_opts = {
        'format': 'b[vcodec~=\'^(h264|avc)\'] / b[ext=mp4]',
        'playlist_items': '1',
        'verbose': True,
    }
    # overall optimal download for transcoding
    ydl_opts_transcode = {
        'format': 'bv*+ba*',
        'playlist_items': '1',
    }

    @staticmethod
    def _fetch(opts: dict, link: str, workdir: str):
        """
        Blocking: download a link into workdir and return (info, filepath).
        The context manager closes yt_dlp's connection pool on exit, which is what
        stops sockets from piling up in CLOSE_WAIT. Run via asyncio.to_thread.
        """
        call_opts = {**opts, 'outtmpl': os.path.join(workdir, '%(id)s.%(ext)s')}
        with yt_dlp.YoutubeDL(call_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            if info and "entries" in info:
                # quote tweets etc: first entry is the desired video
                info = next(iter(info["entries"]))
            downloads = info.get("requested_downloads")
            if downloads and downloads[0].get("filepath"):
                path = downloads[0]["filepath"]
            else:
                path = ydl.prepare_filename(info)
        return info, path

    @staticmethod
    def _transcode(src: str, dst: str) -> None:
        """Blocking: transcode to h264/aac mp4. Run via asyncio.to_thread."""
        ffmpeg.input(src).output(dst, vcodec='libx264', acodec='aac').run(overwrite_output=True)

    @commands.command(name="download", aliases=["dl"])
    async def download(self, ctx: commands.Context):
        # Split message up via spaces and parse for link
        link = ""
        for part in ctx.message.content.split():
            if part.startswith('https://'):
                link = part
        if not link:
            await ctx.reply("I couldn't find a link in your message!")
            return
        # Everything (download, transcode output) lives in this directory, which is
        # deleted automatically when the block exits, on success, return, or exception.
        # It also isolates concurrent !dl calls from each other.
        with tempfile.TemporaryDirectory(prefix="swannydl_") as workdir:
            filelimit= '%.1f' % float(ctx.filesize_limit/1000000) + 'MB'
            logging.info("Downloading %s  Size limit is %s", link, filelimit)

            # First try the discord-friendly format so no transcode is needed
            try:
                info, inputfile = await asyncio.to_thread(self._fetch, self.ydl_opts, link, workdir)
            except Exception:
                logging.info("Available format not found, forcing a transcode")
                try:
                    info, inputfile = await asyncio.to_thread(self._fetch, self.ydl_opts_transcode, link, workdir)
                except Exception as e:
                    logging.warning("yt_dlp failed for %s: %s", link, e)
                    await ctx.reply("Was unable to download this file, double check your link and try again")
                    return

                # if the file is too big before transcode, don't even bother with transcode
                if os.path.getsize(inputfile) > ctx.filesize_limit:
                    await ctx.reply("File is too large, unable to embed")
                    return

                transcoded = os.path.join(workdir, info['id'] + ".transcode.mp4")
                try:
                    await asyncio.to_thread(self._transcode, inputfile, transcoded)
                except Exception as e:
                    logging.warning("ffmpeg failed for %s: %s", link, e)
                    await ctx.reply("Was unable to transcode this file")
                    return
                inputfile = transcoded

            try:
                if os.path.getsize(inputfile) > ctx.filesize_limit:
                    await ctx.reply("File is too large, unable to embed")
                else:
                    await ctx.reply(file=File(inputfile))
            except Exception as e:
                logging.warning("Unable to attach file: %s", e)
                await ctx.reply("Unable to attach file")


async def setup(bot):
    await bot.add_cog(video_cog(bot=bot))