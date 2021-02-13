import discord
import secrets
import sqlite3


client = discord.Client()


@client.event
async def on_ready():
    client.dbconn = sqlite3.connect('main.db')
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Game(name='such pico, much con'))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!nping'):
        await message.channel.send('npong!')


@client.event
async def on_raw_reaction_add(payload):
    pass

client.run(secrets.token)
