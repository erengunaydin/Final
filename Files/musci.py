import discord
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('discord_token')
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents)

    voice_clients = {}
    yt_dl_options = {"format": "bestaudio/best"}
    ytdl = yt_dlp.YoutubeDL(yt_dl_options)

    ffmpeg = {'options': 'vn'}

    @client.event
    async def on_ready():
        print(f'{client.user} is now jamming')

        @client.event
        async def on_message(message):
            if message.contnet.startwith("?play"):
                try:
                    voice_client = await message.author.voice.channel.connect()
                    voice_clients=[voice_client.guild.id] = voice_client
                    
