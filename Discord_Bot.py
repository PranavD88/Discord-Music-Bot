import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import os

#Intents in discord are the specific events that the bot will be utilizing and recieving, instead of the bot recieving every event occuring in the server
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents) # Users will use '!' as the prefix to call upon the bot

# FFmpeg streaming options
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

song_queue = []

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")


# Joins voice channel so that the bot is ready to function in playing music
@bot.command()
async def join(ctx):
    if ctx.author.voice: # Checks for if user is in a voice channel and moves to that channel if already in one
        channel = ctx.author.voice.channel 
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
            await ctx.send(f"Moved to {channel.name}")
        else:
            await channel.connect()
            await ctx.send(f"Joined {channel.name}")
    else:
        await ctx.send("You need to be in a voice channel to use this command")


# Leave a voice channel
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected from the voice channel")
    else:
        await ctx.send("I'm not in a voice channel")


# Play a song from YouTube
@bot.command()
async def play(ctx, *, url=None): # Plays music from a youtube link
    if not ctx.voice_client:
        await ctx.send("I'm not in a voice channel, Use `!join` first")
        return
    # If nothing is provided, the bot will ask for a link or term
    if url is None:
        await ctx.send("Please provide a YouTube URL or search term")
        return

    YDL_OPTIONS = {"format": "bestaudio", "noplaylist": "True"}

    try:
        # Search for the URL if a keyword is provided (instead of a link, such as !play heartbeat)
        if not url.startswith("http"):
            url = await search_youtube(url)

        # Function to show thumbnail of youtube video when requesting to play a song
        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info["url"]
            title = info["title"]
            thumbnail = info["thumbnail"]  # Thumbnail URL

        # If a song is already playing when a !play is performed, it will add it to queue () - this is why song_queue = [] was specified earlierr
        if ctx.voice_client.is_playing():
            song_queue.append((url2, title, thumbnail))
            embed = discord.Embed(
                title="Added to Queue",
                description=f"[{title}]({url})",
                color=discord.Color.blue(),
            )
            embed.set_thumbnail(url=thumbnail)
            await ctx.send(embed=embed)
        else:
            source = await discord.FFmpegOpusAudio.from_probe(
                url2,
                executable="C:\\Users\\WinterSongMC\\Downloads\\ffmpeg-7.1-essentials_build\\ffmpeg-7.1-essentials_build\\bin\\ffmpeg.exe", # Again, ran into multiple issues with running ffmpeg with the bot so I had to specify the file path
            )
            ctx.voice_client.stop()
            ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(ctx)))

            embed = discord.Embed(
                title="Now Playing",
                description=f"[{title}]({url})",
                color=discord.Color.green(),
            )
            embed.set_thumbnail(url=thumbnail)
            await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send("An error occurred while trying to play the audio") # If any error occurrs, it is handled by this
        print(f"Error: {e}")


# Plays the next song in the queue
async def play_next(ctx):
    if song_queue:
        url2, title, thumbnail = song_queue.pop(0)
        source = await discord.FFmpegOpusAudio.from_probe(
            url2,
            executable="C:\\Users\\WinterSongMC\\Downloads\\ffmpeg-7.1-essentials_build\\ffmpeg-7.1-essentials_build\\bin\\ffmpeg.exe",
            **FFMPEG_OPTIONS
        )
        ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(ctx)))

        embed = discord.Embed(
            title="Now Playing",
            description=f"[{title}]({url2})",
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=thumbnail)
        await ctx.send(embed=embed)


# Pauses the song
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Paused song")
    else:
        await ctx.send("Nothing is playing right now")


# Resumes song
@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumed song")
    else:
        await ctx.send("Nothing is paused")


# Stop the songs
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("Exited out of the songs")
    else:
        await ctx.send("I'm not in a voice channel")


# Skip the current song
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped the current song")
    else:
        await ctx.send("No song to skip")


# Show the current queue
@bot.command()
async def queue(ctx):
    if song_queue:
        queue_list = "\n".join([f"{i+1}. {title}" for i, (_, title) in enumerate(song_queue)])
        await ctx.send(f"Current Queue:\n{queue_list}")
    else:
        await ctx.send("The queue is empty")


# Helper function to search and play the first youtube link when given terms on !play instead of a link
async def search_youtube(query):
    YDL_OPTIONS = {"format": "bestaudio", "noplaylist": "True"}
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)
        if info["entries"]:
            return info["entries"][0]["webpage_url"]
        return None

from dotenv import load_dotenv
import os

load_dotenv()

# Bot Token
bot.run(os.getenv("Discord_Bot_Token"))

