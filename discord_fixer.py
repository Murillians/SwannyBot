import logging
import os
import time
from datetime import datetime
from datetime import timedelta
import discord
import requests
from discord.ext import commands
from discord import app_commands,File
import swannybottokens
import ffmpeg
from PIL import Image
class DiscordFixer_cog(commands.Cog,name="DiscordFixer_cog"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name = "Fix Message For Discord",
            callback=self.menu_fix
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def menu_fix(self,interaction: discord.Interaction, message:discord.Message):
        for attachment in message.attachments:
            await attachment.save(attachment.filename)
            filename=attachment.filename.split(".")[0]
            fileextension=attachment.filename.split(".")[1]
            convertedfile=None
            try:
                if "video" in attachment.content_type:
                    print("this is a video file!")
                    if(self.video_fixer(filename,fileextension)):
                        convertedfile = filename + ".mp4"
                if "image" in attachment.content_type:
                    print("this is a image file!")
                    if(self.image_fixer(filename,fileextension)):
                        convertedfile = filename + ".jpg"
                if "audio" in attachment.content_type:
                    print("this is an audio file!")
                    if (self.audio_fixer(filename,fileextension)):
                        convertedfile= filename +".mp3"

            except Exception as e:
                os.remove(attachment.filename)
                os.remove(convertedfile)
                await message.reply("Was unable to fix this file!")
                print(e)
                break
            try:
                filesize = os.path.getsize(attachment.filename)
                if filesize > 25000000:
                    await message.reply("File is too large, unable to embed")
                os.remove(attachment.filename)
                await message.reply(file=File(convertedfile))
                os.remove(convertedfile)
            except Exception as e:
                await message.reply("Was unable to fix this file!")
                print(e)

    def video_fixer(self,filename,fileextension):
        temp = ffmpeg.input(filename+"."+fileextension).output((filename + ".mp4"), vcodec='libx264', acodec="aac").run()
        return temp
    def image_fixer(self,filename,fileextension):
        convertedimage=Image.open(filename+"."+fileextension)
        convertedimage=convertedimage.convert("RGB")
        convertedimage.save(filename+".jpg")
    def audio_fixer(self,filename,fileextension):
        temp = ffmpeg.input(filename+"."+fileextension).output((filename+".mp3"), acodec='libmp3lame').run()
        return temp

    @commands.command(name="oldfix")
    async def fix(self,ctx: discord.ext.commands.Context):
        print (ctx)
        calling_message=ctx.message
        tmpctx=await ctx.from_interaction(ctx.interaction)
        fix_message = await ctx.channel.fetch_message(tmpctx.message.reference.message_id)
        #print(fix_message)
        await ctx.send(fix_message.content+" is now Fixed!")



async def setup(bot):
    await bot.add_cog(DiscordFixer_cog(bot=bot))