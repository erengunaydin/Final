import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv

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

    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.25"'}

    @client.event
    async def on_ready():
        print(f'{client.user} is now playing music')

    aysnc def play_next(ctx):
        if queues[ctx.guild.id] != []:
            link = queues[ctx.guild.id].pop(0)
            await play(ctx, link)

    @client.command(name="play")
    async def play(ctx, link):
        try:
            voice_client = await ctx.author.voice.channel.connect()
            voice_clients[voice_client.guild.id] = voice_client
        except Exception as e:
            print(e)

        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(link, download=False))

            song_title = data.get('title', 'Unknown Song')
            song_url = data['url']
            
            player = discord.FFmpegOpusAudio(song_url, **ffmpeg_options)

            voice_clients[ctx.guild.id].play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), client.loop)
        
            embed = discord.Embed(
            title="Now Playing",
            description=f"{song_title}",
            color=discord.Color.blue()
        )
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
    
    @client.command(name="pause")
    async def pause(ctx):
        try:
            voice_clients[ctx.guild.id].pause()
            embed = discord.Embed(
                title="Music Paused 🎵",
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
            embed = discord.Embed(
                title="Music Stopped ⏹️",
                description="Goodbye!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
    
    @client.command(name="queue")
    async def queue(ctx, url):
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []
        queues[ctx.guild.id].append(url)
        await ctx.send("Added to queue!")
    


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    client.run(TOKEN)