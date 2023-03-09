import asyncio
import logging

import discord
from discord.ext import commands
from wavelink.ext import spotify

import swannybottokens
import wavelink


class music_cog(commands.Cog):

    disconnectTimers = set()

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # stores guild ID w/ wavelink player object
        self.guildPlayers = {}
        bot.loop.create_task(self.connect_nodes())

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        # Event fired when a node has finished connecting
        print(f'Node <{node.identifier}> is ready')

    async def connect_nodes(self):
        # to connect to wavelink nodes
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot=self.bot,
                                            host='127.0.0.1',
                                            port=2333,
                                            password=swannybottokens.WavelinkPassword,
                                            spotify_client=spotify.SpotifyClient(client_id=swannybottokens.SpotifyID,
                                                                                 client_secret=swannybottokens.SpotifySecret))

    # connect function, mostly helper
    @commands.command()
    async def connect(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        try:
            channel = channel or ctx.author.voice.channel
        except AttributeError:
            return await ctx.send("Connect to a voice channel!")
            raise Exception()
        vc: wavelink.Player = await channel.connect(cls=wavelink.Player)
        return vc

    # Pause Function
    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        wavelinkPlayer = self.guildPlayers[ctx.guild.id]
        if not wavelinkPlayer.is_paused():
            await wavelinkPlayer.pause()
        else:
            await wavelinkPlayer.resume()

    # Resume Function
    @commands.command(name="resume", aliases=["r"], help="Resumes playing the current song")
    async def resume(self, ctx, *args):
        wavelinkPlayer = self.guildPlayers[ctx.guild.id]
        if wavelinkPlayer.is_paused():
            await wavelinkPlayer.resume()

    # Skip Function
    @commands.command(name="skip", aliases=["s"], help="Skips the song currently playing")
    async def skip(self, ctx, *args):
        wavelinkPlayer = self.guildPlayers[ctx.guild.id]
        if wavelinkPlayer is not None and wavelinkPlayer.is_playing():
            await wavelinkPlayer.stop()

    # Queue Function
    # todo: FIX
    @commands.command(name="queue", aliases=["q"], help="Displays all the songs currently in queue")
    async def queue(self, ctx):
        wavelinkPlayer = self.guildPlayers[ctx.guild.id]
        currentQueue = wavelinkPlayer.queue
        retval = "Up Next: \n"
        for i in range(0, len(wavelinkPlayer.queue)):
            if i > 4:
                break
            retval += currentQueue[i].title + '\n'
        if retval != "Up Next: \n":
            await ctx.send(retval)
        else:
            await ctx.send("No music in the queue.")

    # Clear Queue Function
    @commands.command(name="clear", aliases=["c", "bin"], help="Stops the current song and clears the queue")
    async def clear(self, ctx, *args):
        wavelinkPlayer = self.guildPlayers[ctx.guild.id]
        if wavelinkPlayer is not None and wavelinkPlayer.is_playing():
            await wavelinkPlayer.stop()
            wavelinkPlayer.queue.clear()
        await ctx.send("Music queue cleared")

    # Leave Function
    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kick the bot from the voice channel")
    async def leave(self, ctx):
        wavelinkPlayer = self.guildPlayers[ctx.guild.id]
        wavelinkPlayer.queue.clear()
        self.guildPlayers.pop(wavelinkPlayer.guild.id)
        await wavelinkPlayer.disconnect()

    ##begin rewrite of event-centric functions
    # play command, should not handle any technical information about playing, only discord channel facing play
    @commands.command(name="play", aliases=["p"], help="Play music! Can handle Spotify, YouTube, and Soundcloud links")
    # Play Function
    async def newplay(self, ctx: commands.Context, *, song: str):
        currentGuild = ctx.author.voice.channel.guild.id
        currentPlayer = None
        # try to get current player, if not found, connect
        if currentGuild in self.guildPlayers:
            currentPlayer: wavelink.Player  = self.guildPlayers[currentGuild]
        else:
            currentPlayer: wavelink.Player = await self.connect(ctx)
            self.guildPlayers[currentGuild] = currentPlayer

        # begin trying to add song to queue
        # what message that gets printed in reply to user play request
        discordMessage = None
        # temp variable to hold messages/check for errors
        tempReturn = None

        tempReturn = await self.spotifyUrlHandler(song, currentPlayer)
        if tempReturn is not None:
            discordMessage = tempReturn

        # check discordMessage to see if we already found a song
        if discordMessage is None:
            tempReturn = await self.soundcloudUrlHandler(song, currentPlayer)
            if tempReturn is not None:
                discordMessage = tempReturn

        if discordMessage is None:
            tempReturn = await self.youtubeUrlHandler(song, currentPlayer)
            if tempReturn is not None:
                discordMessage = tempReturn

        # send error if none of the parsers could find a song
        if tempReturn is None:
            await ctx.reply("Unable to find your song!")
            return
        try:
            if currentPlayer.is_playing() is False:
                track = await currentPlayer.queue.get_wait()
                await currentPlayer.play(track)
        except Exception as e :
            print(e)
            pass
        if isinstance(discordMessage,discord.Embed) is True:
            await ctx.send(embed=discordMessage)
            return
        await ctx.reply(discordMessage)

    # Helper function to decode Spotify tracks, will queue up the appropriate track/playlist/album/artist and return a formatted message
    # has to search the spotify url and load from youtube
    async def spotifyUrlHandler(self, spotifyLink, wavelinkPlayer):
        formattedReturnMessage = None
        decodedUrl = spotify.decode_url(spotifyLink)
        queueError = None
        if decodedUrl is not None:
            if decodedUrl['type'] is spotify.SpotifySearchType.track:
                track = await spotify.SpotifyTrack.search(query=decodedUrl["id"], type=decodedUrl["type"],
                                                          return_first=True)
                queueError = await self.addTrackToQueue(wavelinkPlayer, track)
                if queueError is None:
                    formattedReturnMessage = str(track.title) + " Has been added to the queue"
                else:
                    return queueError
            elif decodedUrl['type'] is spotify.SpotifySearchType.album:
                trackCount = 0
                #playlist detected, add every track in that playlist to the queue.
                async for track in spotify.SpotifyTrack.iterator(query=decodedUrl['id'], type=spotify.SpotifySearchType.album, partial_tracks=True):
                    queueError = await self.addTrackToQueue(wavelinkPlayer, track)
                    if queueError is None:
                        trackCount+=1
                        pass
                    else:
                        return discord.Message("Could not add songs past "+ track.title+" in that album, sorry lol")
                formattedReturnMessage = str(trackCount)+" songs added to queue!"
            elif decodedUrl['type'] is spotify.SpotifySearchType.playlist:
                trackCount = 0
                #playlist detected, add every track in that playlist to the queue.
                async for track in spotify.SpotifyTrack.iterator(query=decodedUrl['id'], type=spotify.SpotifySearchType.playlist, partial_tracks=True):
                    queueError = await self.addTrackToQueue(wavelinkPlayer, track)
                    if queueError is None:
                        trackCount+=1
                        pass
                    else:
                        return discord.Message("Could not add songs past "+ track.title+" in that playlist, sorry lol")
                formattedReturnMessage = str(trackCount)+" songs added to queue!"
            else:
                formattedReturnMessage = discord.Message("SwannyBot is unable to play this type of Spotify URL")
        return formattedReturnMessage

    async def youtubeUrlHandler(self, inputUrl, wavelinkPlayer):
        formattedReturnMessage = None
        track=None
        # YouTube Playlist Handler
        #TODO: possibly make youtube playlists load as partial tracks
        try:
            playlist = await wavelink.YouTubePlaylist.search(inputUrl)
            trackCount = 0
            for track in playlist.tracks:
                queueError = await self.addTrackToQueue(wavelinkPlayer, track)
                if queueError is None:
                    trackCount+=1
                    pass
                else:
                    return discord.Message("Could not add songs past " + track.title + " in that playlist, sorry lol")
            formattedReturnMessage = str(trackCount) + " songs added to queue!"
        except:
            pass
        #YouTube Music Handler TODO: fix
        if formattedReturnMessage is not None:
            track = await wavelink.YouTubeMusicTrack.search(query=inputUrl,return_first=True)
            queueError = await self.addTrackToQueue(wavelinkPlayer, track)
            if queueError is None:
                formattedReturnMessage = discord.Embed(
                    title=track.title + " added to queue",
                    url=track.uri
                ).set_image(url=track.thumb).set_thumbnail(url=track.thumbnail)
            else:
                return queueError
            return formattedReturnMessage
        # YouTube song/url Handler
        if formattedReturnMessage is None:
            #try to search a youtube URL first
            trackList = await wavelink.NodePool.get_node().get_tracks(query=inputUrl,cls=wavelink.Track)
            #if empty, search youtube, otherwise get the track
            if len(trackList) == 0:
                #not a youtube url, go search the song and give back the first result
                track = await wavelink.YouTubeTrack.search(query=inputUrl, return_first=True)
            else:
                track=trackList[0]
            queueError = await self.addTrackToQueue(wavelinkPlayer, track)
            if queueError is None:
                formattedReturnMessage = discord.Embed(
                    title=track.title + " added to queue",
                    url=track.uri
                )
                    #.set_image(url=track.thumb).set_thumbnail(url=track.thumbnail)
            else:
                return queueError
        return formattedReturnMessage

    async def soundcloudUrlHandler(self, song, wavelinkPlayer):
        return None

    # helper that adds track to the END of the queue
    async def addTrackToQueue(self, wavelinkPlayer: wavelink.Player, track):
        try:
            await wavelinkPlayer.queue.put_wait(track)
        except wavelink.QueueException:
            return "Queue error, unable to add song"
        except wavelink.QueueFull:
            return "Queue full, unable to add song"
        except Exception as e:
            logging.error(e)
            return "Unspecified error, check error logs"
        return None
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        currentQueue = player.queue
        if currentQueue.count > 0:
            nextSong=await currentQueue.get_wait()
            await player.play(nextSong)
        else:
            task = asyncio.create_task(self.timeout(player))
            task.add_done_callback(self.disconnectTimers.discard)
            self.disconnectTimers.add(task)


#TODO:Fix timeout code not stopping older timeouts correctly
    async def timeout(self,player:wavelink.Player):
        await asyncio.sleep(600)
        if player.is_playing() is not True:
            self.guildPlayers.pop(player.guild.id)
            await player.disconnect()

    @commands.Cog.listener()
    async def on_wavelink_websocket_closed(player: wavelink.Player, reason, code):
        logging.info("wavelink websocket closed, Reason: " + reason + " Code: " + code)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(player: wavelink.Player, track: wavelink.Track, error):
        logging.info("wavelink track error, Error: " + error + " track: " + track)


    @commands.Cog.listener()
    async def on_wavelink_track_stuck(player: wavelink.Player, track: wavelink.Track, threshold):
        logging.info("wavelink track stuck, Threshold: " + threshold + " track: " + track)


