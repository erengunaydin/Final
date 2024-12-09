import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
import random

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('discord_token')
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix=".", intents=intents)

    queues = {}
    voice_clients = {}
    yt_dl_options = {"format": "bestaudio/best"}
    ytdl = yt_dlp.YoutubeDL(yt_dl_options)

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -filter:a "volume=0.25"'
    }

    @client.event
    async def on_ready():
        print(f'{client.user} is now playing music!')

    async def play_next(ctx):
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []

        if queues[ctx.guild.id]:
            link = queues[ctx.guild.id].pop(0)
            await play(ctx, link)
        else:
            if ctx.guild.id in voice_clients:
                await voice_clients[ctx.guild.id].disconnect()
                del voice_clients[ctx.guild.id]

    @client.command(name="play")
    async def play(ctx, link):
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []

        try:
            if ctx.guild.id not in voice_clients:
                voice_client = await ctx.author.voice.channel.connect()
                voice_clients[ctx.guild.id] = voice_client

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(link, download=False))

            song_title = data.get('title', 'Unknown Song')
            song_url = data['url']
            thumbnail_url = data.get('thumbnail', None)
            
            player = discord.FFmpegOpusAudio(song_url, **ffmpeg_options)

            if voice_clients[ctx.guild.id].is_playing():
                voice_clients[ctx.guild.id].stop()

            voice_clients[ctx.guild.id].play(
                player, 
                after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), client.loop)
            )
        
            embed = discord.Embed(
                title="Now Playing 🎶",
                description=f"{song_title}",
                color=discord.Color.blue()
            )
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Error in play command: {e}")
            await ctx.send(f"An error occurred while trying to play the song: {e}")

    @client.command(name="skip")
    async def skip(ctx):
        try:
            if ctx.guild.id in voice_clients and voice_clients[ctx.guild.id].is_playing():
                embed = discord.Embed(
                    title="Skipped 🎶",
                    description="Current song has been skipped. Playing the next song...",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                
                voice_clients[ctx.guild.id].stop()
            else:
                embed = discord.Embed(
                    title="No Song Playing ❌",
                    description="There is no song currently playing to skip.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error in skip command: {e}")
            await ctx.send(f"An error occurred while skipping: {e}")

    @client.command(name="queue")
    async def queue_cmd(ctx, url):
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []

        queues[ctx.guild.id].append(url)

        embed = discord.Embed(
            title="Song Added to Queue! 🎶",
            description=f"The song has been added to the queue. Position: {len(queues[ctx.guild.id])}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @client.command(name="viewqueue")
    async def view_queue(ctx):
        if ctx.guild.id in queues and queues[ctx.guild.id]:
            embed = discord.Embed(
                title="Current Music Queue 📋",
                color=discord.Color.green()
            )
            
            for i, song_url in enumerate(queues[ctx.guild.id][:10], 1):
                try:
                    loop = asyncio.get_event_loop()
                    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(song_url, download=False))
                    song_title = data.get('title', 'Unknown Song')
                    embed.add_field(name=f"#{i}", value=song_title, inline=False)
                except Exception as e:
                    embed.add_field(name=f"#{i}", value=f"Could not fetch song info: {song_url}", inline=False)
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Queue is Empty 🚫",
                description="There are no songs in the queue.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @client.command(name="clearqueue")
    async def clearqueue(ctx):
        if ctx.guild.id in queues:
            queues[ctx.guild.id].clear()
            embed = discord.Embed(
                title="Queue Cleared 🧹",
                description="The music queue has been cleared!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="No queue to clear ❌",
                description="There is no queue to clear.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed) 
    
    @client.command(name="pause")
    async def pause(ctx):
        try:
            voice_clients[ctx.guild.id].pause()
            embed = discord.Embed(
                title="Music Paused 🎶",
                description="The music has been paused. Use the `.resume` command to continue playing.",
                color=discord.Color.yellow()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
    
    @client.command(name="resume")
    async def resume(ctx):
        try:
            voice_clients[ctx.guild.id].resume()
            embed = discord.Embed(
                title="Music Resumed 🎶",
                description="Resuming...",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)

    @client.command(name="stop")
    async def stop(ctx):
        try:
            voice_clients[ctx.guild.id].stop()
            await voice_clients[ctx.guild.id].disconnect()
            del voice_clients[ctx.guild.id]
            embed = discord.Embed(
                title="Music Stopped ⏹️",
                description="Goodbye!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)

    @client.command(name="shuffle")
    async def shuffle(ctx):
        if ctx.guild.id in queues and queues[ctx.guild.id]:
            random.shuffle(queues[ctx.guild.id])
            embed = discord.Embed(
                title="Queue Shuffled 🔀",
                description="The queue has been shuffled!",
                color=discord.Color.purple()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("There is no queue to shuffle!")

    @client.command(name="commands")
    async def help_command(ctx):
        embed = discord.Embed(
            title="🎵 Music Commands 🎵",
            description="Here are all the available commands!",
            color=discord.Color.blue()
        )

        commands_list = [
            {
                "name": "play <YouTube URL>",
                "value": "Plays a song from the provided YouTube URL or adds it to the queue."
            },
            {
                "name": "queue <YouTube URL>",
                "value": "Adds a song to the queue without immediately playing it."
            },
            {
                "name": "viewqueue",
                "value": "Shows the current music queue (first 10 songs)."
            },
            {
                "name": "skip",
                "value": "Skips the currently playing song and plays the next song in the queue."
            },
            {
                "name": "pause",
                "value": "Pauses the currently playing song."
            },
            {
                "name": "resume",
                "value": "Resumes playing the paused song."
            },
            {
                "name": "stop",
                "value": "Stops the music and disconnects the bot from the voice channel."
            },
            {
                "name": "clearqueue",
                "value": "Removes all songs from the current queue."
            },
            {
                "name": "shuffle",
                "value": "Randomly shuffles the songs in the current queue."
            }
        ]
        
        for cmd in commands_list:
            embed.add_field(name=cmd['name'], value=cmd['value'], inline=False)
        
        embed.set_footer(text="Use a '.' before each command. Example: .play")
        
        await ctx.send(embed=embed)

    client.run(TOKEN)