import asyncio
import logging
import datetime

import discord
from discord.ext import commands
from wavelink.ext import spotify

import swannybottokens
import wavelink


async def timeout(player: wavelink.Player):
    await asyncio.sleep(600)
    if player.is_playing() is not True:
        await player.disconnect()


class music_cog(commands.Cog):
    node = wavelink.Node(uri='127.0.0.1:2333', password=swannybottokens.WavelinkPassword)

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self.connect_nodes())

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        # Event fired when a node has finished connecting
        print(f'Node <{node.id}> is ready')

    async def connect_nodes(self) ->None:
        # to connect to wavelink nodes
        await self.bot.wait_until_ready()
        await wavelink.NodePool.connect(client=self.bot,nodes=[self.node],spotify=spotify.SpotifyClient(client_id=swannybottokens.SpotifyID,
                                           client_secret=swannybottokens.SpotifySecret))

    # connect function, mostly helper
    @commands.command()
    async def connect(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        try:
            channel = channel or ctx.author.voice.channel
        except AttributeError:
            return await ctx.send("Connect to a voice channel!")
        vc: wavelink.Player = await channel.connect(cls=wavelink.Player)  # type: ignore
        return vc

    # Pause Function
    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        wavelinkPlayer = self.getCurrentPlayer(ctx)
        if not wavelinkPlayer.is_paused():
            await wavelinkPlayer.pause()
        else:
            await wavelinkPlayer.resume()

    # Resume Function
    @commands.command(name="resume", aliases=["r"], help="Resumes playing the current song")
    async def resume(self, ctx, *args):
        wavelinkPlayer = self.getCurrentPlayer(ctx)
        if wavelinkPlayer.is_paused():
            await wavelinkPlayer.resume()

    # Skip Function
    @commands.command(name="skip", aliases=["s"], help="Skips the song currently playing")
    async def skip(self, ctx, *args):
        wavelinkPlayer = self.getCurrentPlayer(ctx)
        if wavelinkPlayer is not None and wavelinkPlayer.is_playing():
            await wavelinkPlayer.stop()

    # Queue Function
    @commands.command(name="queue", aliases=["q"], help="Displays all the songs currently in queue")
    async def queue(self, ctx):
        wavelinkPlayer = self.getCurrentPlayer(ctx)
        currentQueue = wavelinkPlayer.queue
        autoplayQueue = wavelinkPlayer.auto_queue
        nowPlaying= None
        if wavelinkPlayer.is_playing():
            nowPlaying = "Now Playing:\n\n"+wavelinkPlayer.current.title + ' - '+wavelinkPlayer.current.author+'\n\n'
        retval = "Up Next: \n\n"
        for i in range(0, len(wavelinkPlayer.queue)):
            if i > 4:
                break
            retval += currentQueue[i].title + '\n'
        if len(autoplayQueue) != 0:
            retval+="\nAutoPlay Queue: \n\n"
            for i in range(0,len(autoplayQueue)):
                if i > 4:
                    break
                retval += autoplayQueue[i].title + ' - ' + autoplayQueue[i].artists[0] + '\n'
        if retval != "Up Next: \n\n" or wavelinkPlayer.is_playing():
            # await ctx.send(str(nowPlaying + retval))
            await ctx.send(embed=discord.Embed(color=0x698BE6,title=wavelinkPlayer.current.title, description=wavelinkPlayer.current.author).set_author(name="Now Playing", icon_url="https://i.imgur.com/GGoPoWM.png").set_footer(text=retval))
        else:
            await ctx.send("No music in the queue.")

    # Clear Queue Function
    @commands.command(name="clear", aliases=["c", "bin"], help="Stops the current song and clears the queue")
    async def clear(self, ctx, *args):
        wavelinkPlayer = self.getCurrentPlayer(ctx)
        if wavelinkPlayer is not None and wavelinkPlayer.is_playing():
            await wavelinkPlayer.stop()
            wavelinkPlayer.queue.clear()
        await ctx.send("Music queue cleared")

    # Leave Function
    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kick the bot from the voice channel")
    async def leave(self, ctx):
        wavelinkPlayer = self.getCurrentPlayer(ctx)
        wavelinkPlayer.queue.clear()
        await wavelinkPlayer.disconnect()

    #command to add song to play next in queue, skips all other songs in queue
    @commands.command(name = "playnext", aliases = ["pn"], help = "Add a song to be next in queue")
    async def playNext(self, ctx: commands.Context, *, song: str):
        tempCtx=ctx
        tempSong=song
        await self.play(tempCtx,song=tempSong)
        player=self.getCurrentPlayer(ctx)
        lastAdded=player.queue.pop()
        player.queue.put_at_front(lastAdded)

    # play command, should not handle any technical information about playing, only discord channel facing play
    @commands.command(name="play", aliases=["p"], help="Play music! Can handle Spotify, YouTube, and Soundcloud links")
    # Play Function
    async def play(self, ctx: commands.Context, *, song: str):
        currentGuild = ctx.author.voice.channel.guild.id
        currentPlayer = self.getCurrentPlayer(ctx)

        # try to get current player, if not found, connect
        if currentPlayer is None:
            currentPlayer: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player) #type: ignore

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
        except Exception as e:
            print(e)
            pass
        if isinstance(discordMessage, discord.Embed) is True:
            await ctx.send(embed=discordMessage)
            return
        await ctx.reply(discordMessage)

    @commands.command(name="autoplay", aliases=["ap"], help="Turn AutoPlay off or on")
    async def autoplay(self, ctx: commands.Context):
        currentPlayer: wavelink.Player = self.getCurrentPlayer(ctx)
        if currentPlayer is None:
            currentPlayer: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player) #type: ignore
        if currentPlayer.autoplay is False:
            currentPlayer.autoplay = True
            await ctx.reply("AutoPlay has been ENABLED for Spotify tracks!")
        else:
            currentPlayer.autoplay = False
            await ctx.reply("AutoPlay has been DISABLED for Spotify tracks!")

    def richEmbed(self, color, title, artists, images, service, song_length):
        return discord.Embed(
            # Color in hexicode
            color=color,
            # Title of track, typically track.name
            title=title,
            # Remaining information, typically track.artists, track.images, "Spotify" or "Youtube", and datetime.timedelta(milliseconds=track.length)
            description=artists).set_thumbnail(url=images).set_author(name=service + " track added to queue").add_field(name="Song Length", value=song_length)


    # Helper function to decode Spotify tracks, will queue up the appropriate track/playlist/album/artist and return a formatted message
    # has to search the spotify url and load from youtube
    async def spotifyUrlHandler(self, spotifyLink:str, wavelinkPlayer):
        formattedReturnMessage = None
        decodedUrl = spotify.decode_url(spotifyLink)
        queueError = None
        if decodedUrl is not None:
            if decodedUrl['type'] is spotify.SpotifySearchType.track:
                track = await spotify.SpotifyTrack.search(query=spotifyLink)
                queueError = await self.addTrackToQueue(wavelinkPlayer, track)
                if queueError is None:
                    #formattedReturnMessage = str(track.title) + " Has been added to the queue"
                    formattedReturnMessage = self.richEmbed(0x00DB00,track.name,track.artists[0],track.images[0],"Spotify",datetime.timedelta(milliseconds=track.length))
                else:
                    return queueError
            elif decodedUrl['type'] is spotify.SpotifySearchType.album:
                trackCount = 0
                # album detected, add every track in that playlist to the queue.
                async for track in spotify.SpotifyTrack.iterator(query=decodedUrl['id'],
                                                                 type=spotify.SpotifySearchType.album):
                    queueError = await self.addTrackToQueue(wavelinkPlayer, track)
                    if queueError is None:
                        trackCount += 1
                        pass
                    else:
                        return discord.Message("Could not add songs past " + track.title + " in that album, sorry lol")
                formattedReturnMessage = str(trackCount) + " songs added to queue!"
            elif decodedUrl['type'] is spotify.SpotifySearchType.playlist:
                trackCount = 0
                playtime = 0
                # playlist detected, add every track in that playlist to the queue.
                async for track in spotify.SpotifyTrack.iterator(query=decodedUrl['id'],
                                                                 type=spotify.SpotifySearchType.playlist):
                    queueError = await self.addTrackToQueue(wavelinkPlayer, track)
                    if queueError is None:
                        trackCount += 1
                        playtime = playtime + track.length
                        pass
                    else:
                        return discord.Message(
                            "Could not add songs past " + track.title + " in that playlist, sorry lol")
                formattedReturnMessage = discord.Embed(color=0x00DB00, title=str(trackCount) + " songs added to queue!").add_field(name="Total Playtime",
                           value=datetime.timedelta(milliseconds=playtime))
            else:
                formattedReturnMessage = discord.Message("SwannyBot is unable to play this type of Spotify URL")
        return formattedReturnMessage

    async def youtubeUrlHandler(self, inputUrl, wavelinkPlayer):
        formattedReturnMessage = None
        track = None
        # YouTube Playlist Handler
        try:
            playlist = await wavelink.YouTubePlaylist.search(inputUrl)
            trackCount = 0
            playtime = 0
            for track in playlist.tracks:
                queueError = await self.addTrackToQueue(wavelinkPlayer, track)
                if queueError is None:
                    trackCount += 1
                    playtime = playtime + track.length
                    pass
                else:
                    return discord.Message("Could not add songs past " + track.title + " in that playlist, sorry lol")
            formattedReturnMessage = discord.Embed(color=0xCC0000, title=str(trackCount) + " songs added to queue!").add_field(name="Total Playtime",value=datetime.timedelta(milliseconds=playtime))
        except:
            pass
        # YouTube song/url Handler
        if formattedReturnMessage is None:
            # try to search a youtube URL first
            trackList = await wavelink.NodePool.get_node().get_tracks(query=inputUrl, cls=wavelink.YouTubeTrack)
            # if empty, search youtube, otherwise get the track
            if len(trackList) == 0:
                # not a youtube url, go search the song and give back the first result
                track = await wavelink.YouTubeTrack.search(inputUrl, return_first=True)
            else:
                track = trackList[0]
            queueError = await self.addTrackToQueue(wavelinkPlayer, track)
            if queueError is None:
                formattedReturnMessage = self.richEmbed(0xCC0000,track.title,track.author,track.thumbnail,"Youtube",str(datetime.timedelta(milliseconds=track.length)))
            else:
                return queueError
        return formattedReturnMessage

        # YouTube Music Handler
        if formattedReturnMessage is None:
            try:
                track = await wavelink.YouTubeMusicTrack.search(inputUrl, return_first=True)
                queueError = await self.addTrackToQueue(wavelinkPlayer, track)
                if queueError is None:
                    formattedReturnMessage = discord.Embed(
                        title=track.title + " added to queue",
                        url=track.uri
                    ).set_image(url=await track.fetch_thumbnail())
                else:
                    return queueError
                return formattedReturnMessage
            except Exception as e:
                pass

    async def soundcloudUrlHandler(self, song, wavelinkPlayer):
        return None

    # helper that adds track to the END of the queue
    async def addTrackToQueue(self, wavelinkPlayer: wavelink.Player, track):
        #UGLY but you HAVE to do a play w/ populate= true for autoplay to work
        #TODO: come back when this feature has been hashed out in Wavelink and make tidier
        if type(track) is spotify.SpotifyTrack and wavelinkPlayer.autoplay is True and wavelinkPlayer.is_playing() is False:
            await wavelinkPlayer.play(track,populate=True)
            return None
        try:
            await wavelinkPlayer.queue.put_wait(track)
        except Exception as e:
            logging.error(e)
            return "Unspecified error, check error logs"
        return None

    @commands.Cog.listener()
    async def on_wavelink_track_end(self,payload: wavelink.TrackEventPayload):
        player=payload.player
        if player.autoplay is True:
            return
        currentQueue = payload.player.queue
        if currentQueue.count >= 1:
            nextSong = await currentQueue.get_wait()
            await player.play(nextSong)
        else:
            await timeout(player)

    # helper function to get
    def getCurrentPlayer(self, ctx: commands.Context):
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild.id)
        return player

    @commands.Cog.listener()
    async def on_wavelink_websocket_closed(payload: wavelink.TrackEventPayload):
        logging.info("wavelink websocket closed, Reason: " + payload.reason + " Code: " + payload.track.title)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(payload: wavelink.TrackEventPayload):
        logging.info("wavelink track error, Reason: " + payload.reason + " track: " + payload.track.title)

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(payload: wavelink.TrackEventPayload):
        logging.info("wavelink track stuck, Reason:: " + payload.reason + " track: " + payload.track.title)

    @commands.command(name="bailiff")
    async def bailiff(self, ctx: commands.Context):
        player= self.getCurrentPlayer(ctx)
        if player:
            baliff = await wavelink.NodePool.get_node().get_tracks(query="https://youtu.be/W9PtKiymAy4", cls=wavelink.YouTubeTrack)
            baliff = baliff[0]
            player.queue.put_at_front(baliff)
            await player.stop()
        else:
            await self.play(ctx,song="https://youtu.be/W9PtKiymAy4")
