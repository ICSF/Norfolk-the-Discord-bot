import discord
import secrets
import sqlite3

from nodules import modmessage, treasure


client = discord.Client()


@client.event
async def on_ready():
    client.dbconn = sqlite3.connect('main.db')
    client.nodules = [x.Nodule(client) for x in (modmessage, treasure)]

    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Game(name='such pico, much con'))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!nping'):
        await message.channel.send('npong!')

    for nodule in client.nodules:
        await nodule.on_message(message)


@client.event
async def on_raw_reaction_add(payload):
    for nodule in client.nodules:
        await nodule.on_raw_reaction_add(payload)

client.run(secrets.token)
