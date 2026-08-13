# Swanny Bot
Swanny Bot is a voice channel music player for Discord.


## How does it work?
- Swanny Bot utilizes an audio player library called [LavaLink](https://github.com/lavalink-devs/Lavalink?tab=readme-ov-file#lavalink) to stream music through. This standalone interface sends to nodes to the [LavaPlayer](https://github.com/lavalink-devs/lavaplayer?tab=readme-ov-file#lavaplayer---audio-player-library-for-discord) as form of an API.
- In order to talk to the Java-based LavaLink with Python, Swanny Bot uses the [WaveLink](https://github.com/PythonistaGuild/Wavelink?tab=readme-ov-file) library as a python wrapper for LavaLink.
- Once we have our commands laid out, we will need to run the `Lavalink.jar` and the bot will connect to the voice channel you are currently in via a command (we designated this to the `!play` function).
- Once it connects, it will begin a play session where any user can add songs to a queue.
- With the play function, end users can search for any song as a message through discord with a query of a song and artist name or with a link. Lavalink can pair with Youtube, Spotify, and Apple Music APIs to find a Playable (a type defined by the wavelink library).
- When a Playable is found, it is added to a Queue object which can be manipulated as well. End users can view the queue at any time with a rich embed through discord every time they call `!queue`.
- Swanny Bot, by default, will play through the entire queue of queries. You can toggle an Auto Queue function in which Swanny Bot can also fetch tracks based on song queries and play off of an auto queue if you use `!autoplay`.
- To ensure the bot is only running when it is being actively called, there is a failsafe implemented for when the queue ends (as in, the music stops playing), in which the bot will say "Bye Bye!" and disconnect from the voice channel.
- An additional failsafe was created for situations in which the bot is playing music but everyone leaves the voice channel, the bot will check every 10 minutes if just the bot is left in the channel and auto disconnect.

## Files

## `Lavalink.jar`
- This is the Lavalink program that needs to be run at the terminal first in order for the bot to connect via a wavelink node.
- To run the program, run a terminal at the folder and input `java -jar Lavalink.jar`
- Requires Java 13 or later to run.

## `application.yml`
- These are the settings for Lavalink as well as the Wavelink key.

## `swanny_bot.py`
- This is the main initializer of the bot. This connects the bot to discord as well as the Lavalink program.

## `music_cog.py`
- This file harbors the commands (see below) for the music player and also contains timeout settings to make sure the bot is not constantly running without activity.

## `help.py`
- This contains the help commands for use within discord in case the end user wants to know what the commands are and also contains a random greeting function when the bot is *thanked*.

## Swanny Bot Commands
As featured in the help command (by sending `!help`  as a message), these are the list of commands you can use for the music player.

`!play`, `!p <link>` - Reads Spotify/Youtube song/playlist link and plays it in your current connected voice channel.
- Will search for the song via youtube if no link is provided.
- Will resume playing the current song if it was paused.
- Will automatically add a song to queue if one is already playing.

`!playnext`, `!pn <link>` - Plays song immediately at the top of a song queue.

`!autoplay`, `!ap` - Enables/Disables an autoplay queue of songs based on a song query. Must enable per play session.
- Songs queued up after autoplay ENABLED will get an generate a list of similar songs that autoplay.
- Songs queued up via `!play`, `!playnext` will take precedence over the autoplay queue.

`!queue`, `!q` - Displays the current music queue.

`!shuffle`, `!shuf` - Shuffles the current music queue.

`!skip`, `!s` - Skips the current song currently playing.

`!clear`, `!c`, `!bin` - Stops the music and clears the queue.

`!leave`, `!disconnect`, `!l`, `!d` - Disconnects SwannyBot from the voice channel.

`!pause` - Pauses the current song being played or resumes if already paused.

`!resume` - Resumes playing the current song.

`!ty_swannybot`, `!tysb` - Thank the bot for his hard work and he will respond a nice message.

### Libraries Used:
**asyncio** - For discord commands

**wavelink** - Python wrapper for Lavalink

**discord, discord commands** - To interact with discord
